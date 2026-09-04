# Testing

This role uses Molecule with the Podman driver for integration testing. The
current scenarios cover Rocky Linux 9 and 10 container workflows. The matrix is
intentionally narrower than the complete list of operating systems supported
by the role.

## Automated test matrix

Platform/image               | Ansible or application versions | Molecule scenarios | Main coverage
-----------------------------|---------------------------------|--------------------|--------------
Rocky Linux 9 UBI init image | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; Dovecot distribution package | `default` | Dovecot installation, configuration, service startup, shared filesystem resources, bind migration, cron, and local Git checkout
Rocky Linux 10 UBI init image | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; Dovecot distribution package | `rocky10` | Same Dovecot and shared-task coverage on Rocky Linux 10 UBI
Rocky Linux 9 UBI init image | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; validation role path | `validation` | Validation success plus invalid bind, TLS, proxy, configuration-path, destructive-path, and symlink-purge guardrails without installation
Rocky Linux 9 UBI init image | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; Dovecot distribution package | `cron_absent` (PR) | Fresh-container explicit absent cron removal with identity-bound marker and unchanged cronie package state
Rocky Linux 9 UBI init image | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; Dovecot distribution package | `global_absent` (scheduled) | Global absent/uninstall cron entry-level removal from unmarked files while preserving unrelated entries

The scenario uses the `docker.io/rockylinux/rockylinux:9-ubi-init` image with Podman,
systemd, and privileged mode so that the bind-mount fixture can exercise
`mount`, `/etc/fstab`, and service lifecycle behavior.

RHEL 9 and RHEL 10 remain supported target operating systems for the role, but
they are not included in the current Molecule matrix because the public UBI
images do not provide the Dovecot package without entitled RHEL repositories.

Global cron `absent` and `uninstall` behavior is covered in the dedicated
`global_absent` scenario with disposable fixtures. The default scenario is the
normal Dovecot baseline only; it does not run destructive lifecycle states.
Preflight validation covers destructive path scope, explicit bind purge opt-in,
and managed configuration-path guardrails. The validation scenario covers
required TLS credentials, equal bind paths, unsafe cleanup paths, and rejected
configuration-tree overrides. Its verify phase compares package, service,
fstab, fixture, and generated-configuration state to ensure the validation
state does not mutate managed Dovecot state; the test harness still writes
disposable snapshots and fixtures. Bind cleanup validation
also checks source/target ownership, rejects duplicate bind targets and
duplicate or mismatched fstab entries, and rejects symlink purge sources. The
minimal validation input includes an absent cron record with only `name`,
`cron_file`, and `state`, preserving the documented removal form. Host-state
cron guardrails are intentionally excluded from this validation-state
scenario; they run in `cron_absent`. Full Dovecot absent/uninstall convergence is not
part of this lightweight validation scenario. The snapshot is paired with
a per-converge token stored in the non-empty `MOLECULE_EPHEMERAL_DIRECTORY`
provided by Molecule; verify requires the exact token match and fails if the
snapshot or current-run token is unavailable. The validation playbooks refuse
to use a shared fallback path, so a fresh Molecule run cannot inherit stale
controller token artifacts. The token is scoped to the container and Molecule
ephemeral directory because this scenario has no externally supplied Molecule
run identifier.

GitHub Actions is configured in `.github/workflows/pr.yml` and
`.github/workflows/scheduled.yml`. Every relevant job checks out the shared task
submodule recursively, installs Podman where needed, creates an isolated Python
environment, and installs the following exact Python CI stack:

```text
ansible-core==2.21.3
molecule==26.8.0
molecule-plugins[podman]==26.7.15
ansible-lint==26.8.0 (syntax/lint jobs)
```

The Molecule jobs separately install these exact Galaxy collections:

```text
ansible.posix==2.2.2
containers.podman==1.20.2
```

The collection pins satisfy the Podman plugin's requirements and use the
published `containers.podman` 1.20.2 release. That release declares
`requires_ansible: ">=2.8"`, so it is compatible with ansible-core 2.21.3.
The published-release metadata was checked at the Galaxy API endpoint
`https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/collections/index/containers/podman/versions/1.20.2/`.
The pull-request `validation` job and scheduled `validation` job install
`molecule/default/collections.yml`. The pull-request baseline job installs the
default manifest, while each scheduled baseline matrix job installs the
manifest for its selected scenario. The syntax/lint (`quality`) jobs do not
install collections because they do not execute collection modules. The
workflow role path is the parent of
`${{ github.workspace }}`, because the checkout directory itself is the role
named `ansible-iac-role-dovecot`; Molecule additionally sets its project role
path in each scenario configuration.

The production-profile lint check deliberately excludes only `tasks/shared/`,
which is the pinned external `ansible-iac-shared-tasks` git submodule. The
submodule has pre-existing upstream lint findings, including command
idempotence and formatting findings; changing or suppressing them is outside
this role's scope. Role-local tasks, documentation examples, and Molecule
scenarios remain linted. This does not claim that the complete repository,
including the external submodule, is lint-clean.

The shared local environment at
`/home/arsi/.local/share/venvs/idarsi-ansible-testing` is not created or
modified by this repository. Its verified Python tools are ansible-core 2.21.3,
Molecule 26.8.0, Molecule Podman plugin 26.7.15, and ansible-lint 26.8.0.
However, its collection search path lists the user collection directory
`/home/arsi/.ansible/collections` before the environment site-packages
directory. That user-level directory contains `containers.podman` 1.8.1 and
therefore shadows the environment's 1.20.2 copy. Local runs must be treated as
using `containers.podman` 1.8.1 unless the effective collection path is checked;
the shared environment is not a reproduction of CI's collection selection.
This repository does not modify the shared environment. CI always installs the
pinned collections into its isolated runner environment.

Pull requests run syntax, production-profile lint, validation, the Rocky Linux
9 `default` baseline, and `cron_absent`. The pull-request workflow is also manually
dispatchable and runs that same fast set. A scheduled run occurs every
Saturday at 03:17 UTC and runs syntax/lint, validation, and the `default`,
`rocky10`, and `global_absent` baseline jobs in parallel. The scheduled workflow is manually
dispatchable and runs the same quality and baseline jobs. No GitHub Actions
job claims RHEL execution; RHEL 9
and 10 remain supported targets but are not automatically tested because the
public UBI images do not provide the Dovecot package without entitled RHEL
repositories.

## Scenario coverage

- `molecule/default` and `molecule/rocky10` validate that the role installs the
  Dovecot package,
  writes the generated configuration, and starts the Dovecot service.
- `molecule/default` is limited to the normal Dovecot baseline convergence and
  verifies the present cron file and its restrictive ownership marker. It does
  not run destructive lifecycle states.
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
  `/etc/cron.d/dovecot_heartbeat` with the expected command and that the role
  creates its restrictive ownership marker. The default converge has no absent
  cron declaration, so its idempotence run remains stable.
- `molecule/validation` rejects duplicate/conflicting `cron_file` declarations
  using `state: validate` without host-state cron operations.
- `molecule/global_absent` exercises global `absent` and `uninstall` with
  disposable unmarked cron files, verifying shared entry-level removal
  preserves unrelated entries instead of deleting the whole file. This does
  not claim full Dovecot lifecycle absent/uninstall coverage.
- `molecule/cron_absent` runs in a fresh Rocky Linux 9 container and verifies an
  explicit absent cron record removes its marked file while leaving the `cronie`
  package state unchanged; it also verifies that a role-managed file deleted
  externally is recreated and its manifest refreshed. Its guardrail tests
  directly exercise the role-local cron cleanup primitive for unowned, changed,
  malformed, and insecure-marker cases. It does not cover full Dovecot
  lifecycle removal.
- The Git fixture creates a local repository inside the test container and
  verifies that the shared Git wrapper clones its committed file to
  `/var/lib/dovecot-config`.
- Converge pre-tasks stop Dovecot, clean stale test mounts and fixture paths,
  and recreate the local Git repository fixture so repeated runs do not depend
  on a previous container state.
- Verify checks the effective Dovecot configuration, generated configuration
  file, package, active service, shared resources, bind state, cron file, and
  Git checkout.

The current scenarios do not test full Dovecot lifecycle `absent` or
`uninstall` convergence, SELinux-specific shared filesystem records, or remote
Git authentication. The `global_absent` scenario covers only shared cron
entry-level behavior for those states.

## Running tests

The CI commands, after the workflow has checked out the repository and
installed its isolated dependencies, are:

```bash
ANSIBLE_ROLES_PATH=".." ansible-playbook --syntax-check \
  -i docs/inventory-example.yml docs/playbook-example.yml
ANSIBLE_ROLES_PATH=".." ansible-lint --profile production
molecule test -s validation
molecule test -s default
molecule test -s rocky10
molecule test -s cron_absent
molecule test -s global_absent
```

The validation, default, and `cron_absent` commands are pull-request coverage;
the Rocky Linux 10 and `global_absent` commands are scheduled/manual coverage.
The workflows install the shared task dependency from
the recursive submodule checkout and use `ansible-galaxy collection install`
with the manifest belonging to each selected scenario.

Run one scenario from the role directory:

```bash
molecule test -s default
```

Run the complete current matrix:

```bash
for scenario in default rocky10 validation cron_absent global_absent; do
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
