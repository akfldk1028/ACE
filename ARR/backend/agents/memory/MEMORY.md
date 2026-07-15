# ARR Global A2A Agents Memory

## 2026-07-07

- Clarified that this folder is required alongside MAAS domain agents.
- Added GitAgent-style root metadata so global infrastructure can be inspected
  with the same folder vocabulary as domain agents.
- Existing runtime files are not moved because Django imports and URL routing
  depend on the current module paths.
