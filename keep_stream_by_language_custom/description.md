This is a fork of [yajrendrag's keep_stream_by_language](https://github.com/yajrendrag/unmanic-plugins) plugin with an added option to **always keep the default (original) audio stream** regardless of its language.

This is useful for libraries with foreign language films where you want to keep the original audio track plus your preferred language (e.g., English).

##### New Option: Keep Default Audio Stream

When enabled (default: on), the plugin will always preserve audio streams marked with the "default" disposition flag, even if their language doesn't match your configured keep list. This ensures the original/primary audio of a film is never stripped.

##### All Other Options

All options from the original plugin are preserved:

- Enter a comma delimited list of audio language codes and a comma delimited list of subtitle language codes — only streams matching these languages are kept.
- You can enter `*` for the language code in one stream type to keep all languages for that type.
- **Keep Default Stream** — always keep the default/original audio stream regardless of language (new in this fork)
- **Keep Commentary** — unchecking removes commentary streams regardless of language
- **Keep Undefined** — keeps streams with no language tags or undefined/unknown tags
- **Fail Safe** — prevents unintentional removal of all audio streams
- **Reorder Kept** — reorders kept audio streams to prioritize the first configured language
- **Prefer 2 Channel or Multichannel** — when reordering, sets the preferred channel layout as default
