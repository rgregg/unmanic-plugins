#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Notify Plex (Targeted Scan)

    Triggers a Plex library scan for only the specific folder that changed,
    instead of scanning the entire library.

    Based on Josh.5's notify_plex plugin.

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
import logging
import os

from unmanic.libs.unplugins.settings import PluginSettings
from plexapi.server import PlexServer

logger = logging.getLogger("Unmanic.Plugin.notify_plex_targeted")


class Settings(PluginSettings):
    settings = {
        'Plex URL':                'http://localhost:32400',
        'Plex Token':              '',
        'Unmanic Path Prefix':     '/library',
        'Plex Path Prefix':        '/data',
        'Notify on Task Failure?': False,
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "Plex URL": {
                "label": "Plex URL",
                "description": "The URL of your Plex server (e.g. http://plex:32400).",
            },
            "Plex Token": {
                "label": "Plex Token",
                "input_type": "password",
                "description": "Your Plex authentication token.",
            },
            "Unmanic Path Prefix": {
                "label": "Unmanic path prefix",
                "description": "The base path where Unmanic sees media files (e.g. /library).\n"
                               "This prefix is replaced with the Plex path prefix to build\n"
                               "the path Plex expects.",
            },
            "Plex Path Prefix": {
                "label": "Plex path prefix",
                "description": "The base path where Plex sees the same media files (e.g. /data).",
            },
            "Notify on Task Failure?": {
                "label": "Notify on task failure?",
                "description": "Also trigger a Plex scan when the task fails.",
            },
        }


def translate_path(file_path, unmanic_prefix, plex_prefix):
    """Replace the Unmanic path prefix with the Plex path prefix."""
    unmanic_prefix = unmanic_prefix.rstrip('/')
    plex_prefix = plex_prefix.rstrip('/')

    if file_path.startswith(unmanic_prefix):
        return plex_prefix + file_path[len(unmanic_prefix):]

    return file_path


def update_plex_targeted(plex_url, plex_token, plex_path):
    """Trigger a Plex scan for just the folder containing the processed file."""
    plex = PlexServer(plex_url, plex_token)
    scan_dir = os.path.dirname(plex_path)

    for section in plex.library.sections():
        for location in section.locations:
            if scan_dir.startswith(location):
                section.update(path=scan_dir)
                logger.info(
                    "Notifying Plex (%s) to scan section '%s' path: %s",
                    plex_url, section.title, scan_dir,
                )
                return True

    logger.warning(
        "No Plex library section found for path '%s'. Falling back to full scan.",
        scan_dir,
    )
    plex.library.update()
    return False


def on_postprocessor_task_results(data):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor movement tasks complete successfully.
        destination_files               - List containing all file paths created by postprocessor file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.

    :param data:
    :return:

    """
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    if not data.get('task_processing_success') and not settings.get_setting('Notify on Task Failure?'):
        return data

    plex_url = settings.get_setting('Plex URL')
    plex_token = settings.get_setting('Plex Token')
    unmanic_prefix = settings.get_setting('Unmanic Path Prefix')
    plex_prefix = settings.get_setting('Plex Path Prefix')

    # Use destination files if available, fall back to source path
    destination_files = data.get('destination_files', [])
    source_path = data.get('source_data', {}).get('abspath', '')

    if destination_files:
        file_path = destination_files[0]
    elif source_path:
        file_path = source_path
    else:
        logger.warning("No file path available. Falling back to full library scan.")
        plex = PlexServer(plex_url, plex_token)
        plex.library.update()
        return data

    plex_path = translate_path(file_path, unmanic_prefix, plex_prefix)
    update_plex_targeted(plex_url, plex_token, plex_path)

    return data
