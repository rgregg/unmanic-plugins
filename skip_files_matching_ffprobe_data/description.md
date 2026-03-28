Inverted version of [limit_library_search_by_ffprobe_data](https://github.com/Unmanic/unmanic-plugins). Instead of queuing files that match, this plugin **skips** files that already meet all your criteria.

Define up to 5 rules, each with a JSONata query and expected values. If **all** rules match, the file is already in your desired state and is skipped. If **any** rule fails, the file is queued for processing.

##### Example Configuration

To skip files that are already HEVC in MKV with a stereo AAC audio track:

| Rule | JSONata Query | Expected Values |
|------|--------------|-----------------|
| 1 | `$.streams[codec_type="video"].codec_name` | `hevc` |
| 2 | `$.format.format_name` | `matroska,webm` |
| 3 | `$.streams[codec_type="audio" and codec_name="aac" and channels=2].codec_name` | `aac` |

- **Rule 1** checks that the video stream is HEVC
- **Rule 2** checks that the container is MKV (Matroska)
- **Rule 3** checks that there is at least one stereo AAC audio stream

A file must match ALL rules to be skipped. If any rule fails, the file is queued for processing.

Leave a rule's fields blank to skip it.
