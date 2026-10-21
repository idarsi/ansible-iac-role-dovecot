# Contributing

## Development

Preserve the documented `iac_blueprint.dovecot` API and validate changes
against the supported Rocky Linux and RHEL 9/10 targets. Keep role behavior
idempotent, fail closed for destructive operations, and update `README.md` and
`TESTING.md` when states, support, prerequisites, or coverage change.

Use the pinned Idarsi Ansible test environment described in
[`TESTING.md`](TESTING.md). Podman is appropriate for application behavior;
SELinux and other host-kernel behavior require the KVM backend. Never report a
UBI container run as SELinux evidence. Do not put subscription credentials,
private keys, or other secrets in the repository or test fixtures.

Before proposing a change, run the relevant syntax/lint checks and focused
dependency-free tests. Molecule/KVM and full-matrix runtime verification belong
in CI or an appropriately provisioned test host; record any unavailable
prerequisite rather than claiming the test passed.

## Pull requests

Describe the API impact, supported platforms, tests run (with exact commands),
and any tests not run with the reason. Keep changes focused and include
documentation and test updates for behavior changes.
