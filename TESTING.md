# Testing

This role uses Molecule with the Podman driver for integration testing. The
current scenarios cover Rocky Linux 9 and 10 container workflows. The matrix is
intentionally narrower than the complete list of operating systems supported
by the role.

## Automated test matrix

Platform/image               | Ansible or application versions | Molecule scenarios | Main coverage
-----------------------------|---------------------------------|--------------------|--------------
Rocky Linux 9 UBI init image | Ansible shared environment; Dovecot distribution package | `default` | Dovecot installation, configuration, service startup, shared filesystem resources, bind migration, cron, and local Git checkout
Rocky Linux 10 UBI init image | Ansible shared environment; Dovecot distribution package | `rocky10` | Same Dovecot and shared-task coverage on Rocky Linux 10 UBI
Rocky Linux 9 UBI init image | Ansible shared environment; validation role path | `validation` | Validation success plus invalid bind, TLS, proxy, configuration-path, destructive-path, and symlink-purge guardrails without installation

The scenario uses the `docker.io/rockylinux/rockylinux:9-ubi-init` image with Podman,
systemd, and privileged mode so that the bind-mount fixture can exercise
`mount`, `/etc/fstab`, and service lifecycle behavior.

RHEL 9 and RHEL 10 remain supported target operating systems for the role, but
they are not included in the current Molecule matrix because the public UBI
images do not provide the Dovecot package without entitled RHEL repositories.

There are currently no separate absent-state scenarios in this repository.
Preflight validation covers destructive path scope, explicit bind purge opt-in,
and managed configuration-path guardrails. The validation scenario covers
required TLS credentials, equal bind paths, unsafe cleanup paths, and rejected
configuration-tree overrides. Its verify phase compares package, service,
fstab, fixture, and generated-configuration state to ensure validation is
non-mutating without assuming Dovecot is installed. Bind cleanup validation
also checks source/target ownership, rejects duplicate bind targets and
duplicate or mismatched fstab entries, and rejects symlink purge sources. The
minimal validation input
includes an absent cron record with only `name`, `cron_file`, and `state`,
preserving the documented removal form. Full absent/uninstall convergence is
not part of this lightweight validation scenario. The snapshot is paired with
a per-converge token stored in Molecule's ephemeral directory; verify requires
the exact token match and fails if the snapshot or token is unavailable.
The token is scoped to the container and Molecule ephemeral directory because
this scenario has no externally supplied Molecule run identifier.

No CI workflow is present in this repository, so all scenarios are manual or
tester-managed executions. The shared task submodule is absent in this
checkout, which prevents local Molecule execution.

## Scenario coverage

- `molecule/default` and `molecule/rocky10` validate that the role installs the
  Dovecot package,
  writes the generated configuration, and starts the Dovecot service.
- `molecule/validation` runs `state: validate` for a minimal blueprint and
  asserts actionable failures for equal bind paths, incomplete TLS, invalid
  proxy URL/port, unsafe destructive paths, symlink purge sources, and unsafe
  configuration-directory/path overrides. It
  also verifies that validation does not create the managed configuration file.
- The `default` and `rocky10` scenarios share the same converge and verify
  playbooks. Each platform validates the shared filesystem wrappers by
  creating a managed directory and an inline-content file, then checking their
  existence and file content.
- The bind fixture starts with a marker file in the legacy target directory.
  It verifies that shared bind migration moves the marker to the real source
  directory, mounts the source at the target path, and writes the expected
  `/etc/fstab` entry.
- The cron fixture verifies that the shared cron wrapper creates
  `/etc/cron.d/dovecot_heartbeat` with the expected command.
- The Git fixture creates a local repository inside the test container and
  verifies that the shared Git wrapper clones its committed file to
  `/var/lib/dovecot-config`.
- Converge pre-tasks stop Dovecot, clean stale test mounts and fixture paths,
  and recreate the local Git repository fixture so repeated runs do not depend
  on a previous container state.
- Verify checks the effective Dovecot configuration, generated configuration
  file, package, active service, shared resources, bind state, cron file, and
  Git checkout.

The current scenarios do not test the destructive `absent` or `uninstall`
flows, SELinux-specific shared filesystem records, or remote Git
authentication. Those should be added as separate scenarios when the role
needs those guarantees.

## Running tests

Run one scenario from the role directory:

```bash
molecule test -s default
```

Run the complete current matrix:

```bash
for scenario in default rocky10 validation; do
  molecule test -s "$scenario" || exit 1
done
```

Run individual Molecule phases while developing:

```bash
molecule syntax -s default
molecule converge -s default
molecule verify -s default
```

The same commands accept `rocky10` or `validation` as the scenario.

Clean up the container explicitly when needed:

```bash
molecule destroy -s default
```

The scenario requires Podman, Ansible, Molecule, the Podman Molecule driver,
and the collections listed in `molecule/default/collections.yml`. The role
uses `ansible.builtin.*` modules at runtime.
