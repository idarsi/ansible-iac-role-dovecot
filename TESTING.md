# Testing

This role uses Molecule with Podman for Rocky Linux integration tests. An
experimental managed-KVM scenario has passed a supervised Rocky 9/10
bind-migration run on `ansible-current`. It is not enabled in CI or the TUI;
full runner acceptance, including concurrent and interrupted runs, is pending. The only
currently supported operating systems are Rocky Linux 9 and 10. Container tests
cover application behavior; they do not provide evidence for SELinux-specific
host behavior.

The dependency-free local guard test checks the rollback task structure for
changed live configuration, changed `.previous` content or metadata, marker
replacement, and cleanup races. It does not simulate an OS-level concurrent
writer; the final `stat`/checksum checks are the production guard.

The Rocky distribution Dovecot package can omit requested protocol or
authentication mechanisms from effective runtime output, depending on the
packaged Dovecot version and modules. The baseline verify phase therefore
asserts the exact requested `protocols` and `auth_mechanisms` lines in the
role-managed file, while checking that effective runtime values are a
non-empty supported subset and retain IMAP, plain authentication, and the
plaintext/TLS security policy.

## Automated test matrix

The declared minimum is ansible-core 2.19.0. Additional compatibility evidence
on ansible-core 2.15.13 includes `podman-validation` and `podman-default`:
`molecule test -s podman-validation` passed in
the shared `ansible-min` environment (ansible-core 2.15.13, Molecule 6.0.3,
and Podman plugin 23.5.0). The tester also ran `podman-default` successfully
through converge, idempotence, verify, and destroy on `ansible-min` and
`ansible-current` (ansible-core 2.20.8). These results exercise the baseline
including bind migration and recovery, but not all role states on 2.15.13;
they do not establish role-wide support on that line. CI continues
to use ansible-core 2.21.3 and does not enforce the declared minimum version.

Platform/image               | Ansible or application versions | Molecule scenarios | Main coverage
-----------------------------|---------------------------------|--------------------|--------------
Rocky Linux 9 UBI init image | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; Dovecot distribution package | `podman-default` | Dovecot installation, configuration, service startup, shared filesystem resources, bind migration, cron, and local Git checkout
Rocky Linux 10 UBI init image | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; Dovecot distribution package | `podman-rocky10` | Same Dovecot and shared-task coverage on Rocky Linux 10 UBI
Rocky Linux 9 UBI init image | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; validation role path | `podman-validation` | Validation success plus invalid bind, TLS, proxy, configuration-path, destructive-path, and symlink-purge guardrails without installation
Rocky Linux 9 UBI init image | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; Dovecot distribution package | `podman-cron_absent` (PR) | Fresh-container explicit absent cron removal with identity-bound marker and unchanged cronie package state
Rocky Linux 9 UBI init image | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; Dovecot distribution package | `podman-global_absent` (scheduled) | Global absent/uninstall refusal and preservation of unowned configuration artifacts, plus cron entry-level removal
Rocky Linux 9 and 10 UBI init images | CI: ansible-core 2.21.3, Molecule 26.8.0, Podman plugin 26.7.15; Dovecot distribution package | `podman-lifecycle` (scheduled) | Full install assertion followed by repeated uninstall; package/service/owned configuration removal and unmanaged fixture preservation
Rocky Linux 9 and 10 KVM guests | Shared `ansible-current` (ansible-core 2.20.8); distribution Dovecot packages | `kvm-bind-migration` (experimental/manual; one successful supervised run) | Both guests passed converge, idempotence, bind migration/fstab, recovery, rollback, and destroy; `ansible-min`/`ansible-next` and runner concurrency/interruption acceptance pending

Global cron `absent` and `uninstall` behavior is covered in the dedicated
`podman-global_absent` scenario with disposable fixtures. Unowned Dovecot configuration
and transaction artifacts are expected to fail closed and remain present. The
`podman-default` scenario runs only the normal Dovecot baseline and second-convergence
idempotence check during converge. Its three test-only configuration transaction
and recovery plays run in verify, after idempotence, so their intentional state
mutations cannot contaminate the baseline idempotence check. It does not run
destructive lifecycle states.
Preflight validation covers destructive path scope, explicit bind purge opt-in,
and managed configuration-path guardrails. The `podman-validation` scenario covers
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
scenario; they run in `podman-cron_absent`. Full Dovecot absent/uninstall convergence is not
part of this lightweight `podman-validation` scenario. `podman-global_absent` checks removal
of owned transaction artifacts and cron entries, but not complete teardown
from a converged installation or package removal. Runtime interruption/recovery
and check-mode/diff-mode behavior also remain gaps; the dependency-free guard
test only inspects rollback structure. The snapshot is paired with
a per-converge token stored in the non-empty `MOLECULE_EPHEMERAL_DIRECTORY`
provided by Molecule; verify requires the exact token match and fails if the
snapshot or current-run token is unavailable. The snapshot is not removed from
the remote host during Molecule cleanup: it lives only in the disposable
container and is removed when Molecule destroys that container. The validation playbooks refuse
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
The pull-request `podman-validation` job and scheduled `podman-validation` job install
`molecule/podman-default/collections.yml`. The pull-request baseline job installs the
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

The shared local environment (for example, `<shared-venv>`) is not created or
modified by this repository. Its verified Python tools are ansible-core 2.21.3,
Molecule 26.8.0, Molecule Podman plugin 26.7.15, and ansible-lint 26.8.0.
However, its collection search path lists the user collection directory
`<user-collection-directory>` before the environment site-packages
directory. The user-level collection directory contains `containers.podman` 1.8.1 and
therefore shadows the environment's 1.20.2 copy. Local runs must be treated as
using `containers.podman` 1.8.1 unless the effective collection path is checked;
the shared environment is not a reproduction of CI's collection selection.
This repository does not modify the shared environment. CI always installs the
pinned collections into its isolated runner environment.

The current checkout has `tasks/shared` initialized at the pinned commit
`d70d58e`. A clean checkout made without submodules cannot run shared-resource
or Molecule execution until the dependency is initialized. For a reproducible
clean checkout, run:

```bash
git submodule sync --recursive
git submodule update --init --recursive
```

CI uses the equivalent `actions/checkout` option `submodules: recursive`.
If the submodule cannot be fetched, role-local syntax and lint checks can still
run, but shared-resource and Molecule coverage remains unavailable. Neither the
shared checkout nor the shared test environment is modified to work around
that portability limitation.

Pull requests run the dependency-free transaction guard check, syntax,
production-profile lint, validation, the Rocky Linux 9 `podman-default` baseline, and
`podman-cron_absent`. The pull-request workflow is also manually
dispatchable and runs that same fast set. A scheduled run occurs every
Saturday at 03:17 UTC and runs syntax/lint, validation, and the `podman-default`,
`podman-rocky10`, `podman-global_absent`, and `podman-lifecycle` baseline jobs in parallel. The scheduled workflow is manually
dispatchable and runs the same quality and baseline jobs. The automated
platform matrix is limited to Rocky Linux 9 and 10. No RHEL coverage or support
is claimed.

## Scenario coverage

- `molecule/podman-default` and `molecule/podman-rocky10` validate that the role installs the
  Dovecot package,
  writes the generated configuration, and starts the Dovecot service.
- `molecule/podman-default` is limited to the normal Dovecot baseline convergence and
  verifies the present cron file, restrictive ownership markers, managed
  configuration permissions, and absence of the transactional candidate after
  convergence. Molecule's idempotence phase covers the unchanged second run;
  it does not run destructive lifecycle states.
- `molecule/podman-validation` runs `state: validate` for a minimal blueprint and
  asserts actionable failures for equal bind paths, incomplete TLS, invalid
  proxy URL/port, unsafe destructive paths, symlink purge sources, and unsafe
  configuration-directory/path overrides. It
  also verifies that validation does not create the managed configuration file.
- The `podman-default`, `podman-rocky10`, and experimental `kvm-bind-migration` scenarios share the same converge and verify
  playbooks. Each platform validates the shared filesystem wrappers by
  creating a managed directory and an inline-content file, then checking their
  existence and file content.
- The bind fixture starts with a marker file in the legacy target directory.
  It verifies that shared bind migration moves the marker to the real source
  directory, mounts the source at the target path, and writes the expected
  `/etc/fstab` entry.
- The cron fixture verifies that the shared cron wrapper creates
  `/etc/cron.d/dovecot_heartbeat` with the expected command and that the role
  creates its restrictive ownership marker. The `podman-default` converge has no absent
  cron declaration, so its idempotence run remains stable.
- `molecule/podman-validation` rejects duplicate/conflicting `cron_file` declarations
  using `state: validate` without host-state cron operations.
- `molecule/podman-validation` also checks the protected `extra_parameters` rejection
  message and newline-injection guard. Configuration rollback on a failed live
  Dovecot validation is fail-closed by task structure, but is not exercised in
  the validation-only container because it has no live configuration tree. The
   forced systemd reload-failure path is exercised in `molecule/podman-default` with a
   test-only one-shot override and verifies restoration of the exact pre-run
   configuration and marker. A later resource failure is intentionally not a
   full transaction: filesystem, Git, cron, bind, and service changes are not
   destructively rolled back. This residual behavior is documented and must be
   checked by operators after a failed convergence.
- `molecule/podman-global_absent` exercises global `absent` and `uninstall` with
  disposable unmarked cron files, verifying shared entry-level removal
  preserves unrelated entries instead of deleting the whole file. It also
  verifies stale managed configuration, `.candidate`, and `.previous`
  transaction artifacts are refused and preserved when unowned. This does not
  claim full Dovecot lifecycle absent/uninstall coverage. Separate plays install
  Dovecot, preserve an unmanaged configuration fixture through two absent runs,
  and verify the package remains absent and service stopped after the fresh
  second invocation. A repeated cron invocation also checks record isolation.
- `molecule/podman-cron_absent` runs in a fresh Rocky Linux 9 container and verifies an
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

The `podman-global_absent` scenario first installs Dovecot and creates an unmanaged
configuration fixture, then runs `absent` twice. It asserts the package stays
absent, the service is not running, and the unmanaged configuration remains
unchanged after the second call. The `podman-lifecycle` scenario tests full
install-to-uninstall on Rocky Linux 9 and 10 Podman systemd containers.
RHEL KVM coverage was removed with RHEL support. Experimental Rocky KVM bind
coverage has one successful supervised `ansible-current` run; minimum/next
lines and full runner concurrency/interruption acceptance remain pending.
Check-mode and diff-mode behavior
remain untested. The current scenarios do not test SELinux-specific shared filesystem
records or remote
Git authentication. The `podman-global_absent` scenario covers transaction-artifact
cleanup and shared cron entry-level behavior for those states, without
installing or removing a complete Dovecot package lifecycle.

## Running tests

The CI commands, after the workflow has checked out the repository and
installed its isolated dependencies, are:

```bash
python tests/test_transaction_guards.py
ANSIBLE_ROLES_PATH=".." ansible-playbook --syntax-check \
  -i docs/inventory-example.yml docs/playbook-example.yml
ANSIBLE_ROLES_PATH=".." ansible-lint --profile production
molecule test -s podman-validation
molecule test -s podman-default
molecule test -s podman-rocky10
molecule test -s podman-cron_absent
molecule test -s podman-global_absent
molecule test -s podman-lifecycle
```

The `podman-validation`, `podman-default`, and `podman-cron_absent` commands are pull-request coverage;
the Rocky Linux 10, `podman-global_absent`, and `podman-lifecycle` commands are
scheduled/manual coverage. The `podman-lifecycle` scenario has passed on Rocky Linux 9
and 10; it is scheduled rather than run on pull requests.
The workflows install the shared task dependency from
the recursive submodule checkout and use `ansible-galaxy collection install`
with the manifest belonging to each selected scenario.
The `podman-default`, `podman-rocky10`, `podman-cron_absent`, and
`podman-global_absent` scenarios install their Galaxy collections into their
own Molecule ephemeral directory, not into the pinned shared environment.
Ansible searches the inherited collection path first (the activated pinned
lane locally, or `~/.ansible/collections` when unset in CI), then this private
directory. These scenarios have no role Galaxy requirements; the removed empty
`requirements.yml` files must not trigger a role install with the collection-
only `--collections-path` option. The experimental managed KVM scenario uses
the activated shared environment's pinned collections without installing
scenario-specific collections.

Run one scenario from the role directory:

```bash
molecule test -s podman-default
```

The experimental KVM bind-migration scenario uses the shared test environment's
supervised managed create/destroy playbooks and Rocky 9/10 Kickstart template, with
passwordless sudo inside each disposable VM. It points directly at the
`podman-default` converge and verify playbooks: existing bind migration,
fstab, resource-failure recovery, and configuration rollback assertions remain
unchanged. The Podman scenarios retain their root-container behavior; only
the KVM inventory opts into sudo and sets `iac_git_become_user: root`, since the
shared Git task otherwise disables inherited privilege escalation for checkout.
The scenario uses direct Rocky 9 and 10
installation sources; they must be available for both guests. Unlike the legacy
KVM launcher, managed mode does not automatically build or select cached base
images. To use already prepared compatible qcow2 images instead, configure
explicit `image_path` inputs for both platforms in place of their
`install_source` and `kickstart` fields. See the shared environment's
`docs/isolated-test-runs.md` for managed image requirements and
`docs/kvm-molecule.md` for preparing sources and host readiness. With the shared
`ansible-current` environment activated and the role submodule initialized,
run the supervised invocation manually from the role directory:

```bash
"${IDARSI_TEST_ENVIRONMENT}/scripts/test-run" run --backend kvm --scenario kvm-bind-migration
```

Do not run this on the shared isolated Podman runner or add privileged,
host-cgroup, or bind-mount capabilities to it. The tester's supervised
`ansible-current` run passed on both Rocky 9 and 10 guests (converge,
idempotence, bind/fstab, recovery, rollback, destroy); managed cleanup
removed both guests for run `22ab93b5-9279-46f1-88bc-6a3023a15ead`.
`ansible-min`, `ansible-next`, concurrent/interrupt runner acceptance, and
explicit cached-image selection remain unverified. The scenario stays
experimental and outside CI, the six-scenario automated Podman matrix, and
the TUI.

Run the complete current matrix:

```bash
for scenario in podman-default podman-rocky10 podman-validation podman-cron_absent podman-global_absent podman-lifecycle; do
  molecule test -s "$scenario" || exit 1
done
```

Run individual Molecule phases while developing:

```bash
molecule syntax -s podman-default
molecule converge -s podman-default
molecule verify -s podman-default
```

The same commands accept `podman-rocky10` or `podman-validation` as the scenario.

Clean up the container explicitly when needed:

```bash
molecule destroy -s podman-default
```

The scenario requires Podman, Ansible, Molecule, the Podman Molecule driver,
and the collections listed in `molecule/podman-default/collections.yml`. The role
uses `ansible.builtin.*` modules at runtime.
