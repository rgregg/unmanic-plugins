#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Skip files already matching FFprobe criteria

    Based on Josh.5's limit_library_search_by_ffprobe_data plugin.
    Inverted logic: define your "done" state and files matching ALL rules are skipped.

    Copyright:
        Copyright (C) 2021 Josh Sunnex

        This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
        Public License as published by the Free Software Foundation, version 3.

        This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
        implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
        for more details.

        You should have received a copy of the GNU General Public License along with this program.
        If not, see <https://www.gnu.org/licenses/>.

"""
import json
import logging
import jsonata

from unmanic.libs.unplugins.settings import PluginSettings

from skip_files_matching_ffprobe_data.lib.ffmpeg import Probe

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.skip_files_matching_ffprobe_data")


class Settings(PluginSettings):
    settings = {
        "rule_1_field":  '',
        "rule_1_values": '',
        "rule_2_field":  '',
        "rule_2_values": '',
        "rule_3_field":  '',
        "rule_3_values": '',
        "rule_4_field":  '',
        "rule_4_values": '',
        "rule_5_field":  '',
        "rule_5_values": '',
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "rule_1_field": {
                "label":       "Rule 1 — JSONata query",
                "description": "A JSONata expression to evaluate against the file's FFprobe data.\n"
                               "Example: $.streams[codec_type=\"video\"].codec_name",
            },
            "rule_1_values": {
                "label":       "Rule 1 — Expected values",
                "description": "Comma-separated values. If the query result contains any of these, rule 1 passes.\n"
                               "Example: hevc,h265",
            },
            "rule_2_field": {
                "label":       "Rule 2 — JSONata query",
                "description": "Leave blank to skip this rule.",
            },
            "rule_2_values": {
                "label":       "Rule 2 — Expected values",
            },
            "rule_3_field": {
                "label":       "Rule 3 — JSONata query",
                "description": "Leave blank to skip this rule.",
            },
            "rule_3_values": {
                "label":       "Rule 3 — Expected values",
            },
            "rule_4_field": {
                "label":       "Rule 4 — JSONata query",
                "description": "Leave blank to skip this rule.",
            },
            "rule_4_values": {
                "label":       "Rule 4 — Expected values",
            },
            "rule_5_field": {
                "label":       "Rule 5 — JSONata query",
                "description": "Leave blank to skip this rule.",
            },
            "rule_5_values": {
                "label":       "Rule 5 — Expected values",
            },
        }


def rule_matches(probe_info, field_query, expected_values):
    """
    Evaluate a single rule: run the JSONata query and check if any expected value is found.

    :return: True if the rule matches (file meets this criterion), False otherwise
    """
    if not field_query or not expected_values:
        return True  # Empty rules are considered passed (no constraint)

    file_path = probe_info.get('format', {}).get('filename', 'unknown')

    try:
        discovered = jsonata.transform(field_query, probe_info)
    except (KeyError, ValueError, Exception) as e:
        logger.debug("Rule query '%s' failed on file '%s': %s", field_query, file_path, e)
        return False

    if discovered is None:
        logger.debug("Rule query '%s' returned None for file '%s'.", field_query, file_path)
        return False

    # Normalize discovered values to a list of strings for comparison
    if isinstance(discovered, str):
        discovered_list = [discovered]
    elif isinstance(discovered, list):
        discovered_list = [str(v) for v in discovered]
    else:
        discovered_list = [str(discovered)]

    # First check if the entire expected string matches (handles values containing commas,
    # e.g. ffprobe returns "matroska,webm" as a single format name)
    if expected_values.strip() in discovered_list:
        logger.debug("Rule matched (exact): query='%s' found '%s' in file '%s'.", field_query, expected_values.strip(), file_path)
        return True

    # Then check individual comma-separated values
    for expected in expected_values.split(','):
        expected = expected.strip()
        if expected and expected in discovered_list:
            logger.debug("Rule matched: query='%s' found '%s' in file '%s'.", field_query, expected, file_path)
            return True

    logger.debug("Rule did not match: query='%s', expected='%s', found='%s' in file '%s'.",
                 field_query, expected_values, discovered_list, file_path)
    return False


def on_library_management_file_test(data):
    """
    Runner function - enables additional actions during the library management file tests.

    Logic: if ALL configured rules match, the file already meets requirements and is SKIPPED.
    If ANY rule fails, the file needs processing and is QUEUED.

    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with
        path                            - String containing the full path to the file being tested.
        issues                          - List of currently found issues for not processing the file.
        add_file_to_pending_tasks       - Boolean, is the file currently marked to be added to the queue for processing.
        priority_score                  - Integer, an additional score that can be added to set the position of the new task in the task queue.
        shared_info                     - Dictionary, information provided by previous plugin runners.

    :param data:
    :return:

    """
    # Get settings
    settings = Settings(library_id=data.get('library_id'))

    # Check if any rules are configured at all
    has_rules = False
    for i in range(1, 6):
        if settings.get_setting(f'rule_{i}_field') and settings.get_setting(f'rule_{i}_values'):
            has_rules = True
            break

    if not has_rules:
        logger.debug("No rules configured. Skipping plugin.")
        return

    # Get the path to the file
    abspath = data.get('path')

    # Get file probe
    probe = Probe.init_probe(data, logger, allowed_mimetypes=['audio', 'video'])
    if not probe:
        return

    probe_info = probe.get_probe()

    # Evaluate all rules — ALL must match for the file to be skipped
    all_rules_match = True
    for i in range(1, 6):
        field = settings.get_setting(f'rule_{i}_field')
        values = settings.get_setting(f'rule_{i}_values')

        # Skip unconfigured rules
        if not field or not values:
            continue

        if not rule_matches(probe_info, field, values):
            all_rules_match = False
            break

    if all_rules_match:
        # File already meets all criteria — skip it
        data['add_file_to_pending_tasks'] = False
        logger.info("File '%s' matches all rules — already meets requirements, skipping.", abspath)
    else:
        # File doesn't meet criteria — queue it for processing
        data['add_file_to_pending_tasks'] = True
        logger.info("File '%s' does not match all rules — queuing for processing.", abspath)

    return data
