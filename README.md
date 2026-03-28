# Unmanic Plugins

Custom [Unmanic](https://github.com/Unmanic/unmanic) plugins for media library processing.

## Plugins

### skip_files_matching_ffprobe_data

Skips files that already match all specified FFprobe criteria (e.g., already HEVC + MKV + AAC stereo). Files that don't match are queued for processing. Based on Josh.5's `limit_library_search_by_ffprobe_data` plugin with inverted logic.

**Type:** Library Management File Test

### keep_stream_by_language_custom

Keeps only audio and subtitle streams matching specified languages, with support for default stream preservation and language reordering. Forked from Josh.5/SenorSmartyPants/yajrendrag's `keep_stream_by_language` plugin.

**Type:** Library Management File Test, Worker Process, Post-processor Task Result

## Installation

Copy the desired plugin folder into your Unmanic plugins directory (`/config/.unmanic/plugins/` inside the container), then enable and configure it via the Unmanic UI.

## Configuration

All plugin settings are configured through the Unmanic web UI. No settings files are included in this repo.
