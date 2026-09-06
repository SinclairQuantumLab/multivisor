# Maintainer documentation

These documents support both human maintainers and coding agents.

- `../README.md`: fork purpose, fixed initial-change summary, and quick start.
- `../PACKAGING.md`: current checkout operations, peer setup, and updates.
- `../AGENTS.md`: current contribution, testing, and branch rules.
- `CHANGELOG.md`: preserved initial engineering history and occasional
  substantial migration notes. Historical instructions may be superseded by
  current operational documents.

## Keep documentation proportional

Update the document that describes the behavior you changed. Routine fixes,
dependency refreshes within the supported policy, and UI maintenance need
clear commit/PR descriptions and relevant verification, not a separate ledger
entry or an expanded README change list.

Write a migration note only when operators must take action or a significant
architecture/runtime decision needs durable explanation. Include the reason,
affected setup, required commands, actual verification, and limitations. Add
detail in proportion to the change; exhaustive file lists and failed-iteration
diaries are not mandatory.

The README's initial-change summary is a dated foundation statement. Do not
append every later change to it. Preserve the original detailed Python
modernization record without treating its format as a template for all work.
