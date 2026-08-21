# Maintainer documentation

The `.agents/` directory contains durable engineering context that should
survive handoffs between maintainers, automation, and AI agents. Despite the
directory name, these documents are written for humans and agents equally.

## Files

- `CHANGELOG.md`: chronological, reproducible change ledger. Each material
  entry explains the baseline, target, implementation, validation, failures,
  operational impact, and rollback procedure.
- `README.md`: this index and maintenance policy.

Repository-wide working rules live in `../AGENTS.md`; do not duplicate them
here unless an entry needs to preserve historical context. Current installer
selection, wheel, extra, and cross-runtime topology rules live in
`../PACKAGING.md`; ledger entries record why those rules changed.

## Maintenance protocol

Add a dated entry at the top of `CHANGELOG.md` for changes to any of these:

- supported Python, Node.js, uv, npm, or Docker runtime versions;
- dependency resolution or lockfile policy;
- package extras, entry points, or generated assets;
- component boundaries or peer-runtime requirements across machines and Python
  environments;
- CI matrix or release workflow;
- public API, protocol, configuration, or UI behavior;
- architecture that future contributors must understand before editing.

Every entry must be self-contained enough that a maintainer starting from the
named baseline commit can reproduce the migration without consulting chat
history. Use exact commands, filenames, expected results, and links to primary
sources. Mark incomplete verification honestly and replace placeholders with
actual results before merging.

For small fixes that do not affect durable engineering context, the Git commit
history remains sufficient and no ledger entry is required.
