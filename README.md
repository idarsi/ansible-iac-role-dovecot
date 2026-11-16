> **Maturity State: Beta**
>
> **RC Readiness: 69%**

ANSIBLE-IAC-ROLE-DOVECOT
========================

Assessment basis: HEAD `a4b4aa4` plus the uncommitted working tree on
`update/dovecot-kvm-bind-migration`, including the initialized `tasks/shared`
submodule at `d70d58e`. This is a **new methodological baseline**, applying
the current maturity rubric's 0, 0.5, or 1 multiplier to each criterion; it
is not a like-for-like decline from the historical 78% assessment. The tester
reported passing `podman-default` converge/idempotence/verify/destroy on
`ansible-min` and `ansible-current`, and one supervised `ansible-current` KVM
run on Rocky 9 and 10 covering bind migration, fstab, rollback, recovery, and
cleanup. These are local results, not CI results at this uncommitted ref.
`meta/main.yml` declares ansible-core 2.19.0 while the pre-existing
Requirements section below says Ansible 2.15 or higher; the 2.15 baseline
pass does not establish role-wide support at 2.15. KVM min/next lanes and
managed-runner concurrency/interruption acceptance remain unverified.

Scorecard (criterion points / maximum):

| Category | Criterion scores | Subtotal |
| --- | --- | ---: |
| Scope and public contract | Purpose 3/3; inputs/states 2.5/5; support 2/4 | 7.5/12 |
| Functional completeness | Core convergence 8/8; lifecycle 3/6; platform/dependencies 1.5/3; failure/rerun 3/3 | 15.5/20 |
| Validation and safety | Preflight 3/6; secure behavior 3/6; destructive guardrails 2.5/5; check/diff 1.5/3 | 10/20 |
| Convergence and recovery | Idempotence 5/5; transitions 2/4; operational recovery 2/4 | 9/13 |
| Automated testing and CI | Static checks 3/3; validation tests 2/4; functional tests 6/6; idempotence 4/4; lifecycle/guardrails 2/4; platform matrix 3/3; CI enforcement 0.5/1 | 20.5/25 |
| Documentation and release hygiene | Operator docs 2/4; test/limitations 2/2; contribution contract 2/2; metadata 1/2 | 7/10 |

Changes from the historical 78.5-point scorecard reflect the stricter
per-criterion multiplier, not necessarily a change in role behavior:

- **Scope:** purpose remains 3/3; inputs/states 4 to 2.5 reflects the
  incomplete contract detail; support 4 to 2 reflects the 2.15 README versus
  2.19 metadata mismatch and incomplete version-boundary evidence.
- **Function:** core convergence 7 to 8 and failure/rerun 2 to 3 reflect
  observed baseline and recovery; lifecycle 5 to 3 reflects incomplete
  transition evidence; platform/dependencies 2 to 1.5 reflects partial
  verification across declared versions.
- **Safety:** preflight 5 to 3 and secure behavior 5 to 3 reflect partial
  evidence for complete validation and security scope; destructive guardrails
  4 to 2.5 reflect incomplete ownership proof for shared Git/filesystem
  cleanup despite stronger configuration/cron/bind checks; check/diff 2 to
  1.5 reflects the documented, untested preview behavior.
- **Recovery:** idempotence 4 to 5 reflects passing second convergence;
  transitions 2 to 2 and operational recovery 2 to 2 retain partial credit
  because the demonstrated rollback does not cover every transition or
  interruption.
- **Testing:** static checks 3 to 3 and idempotence 4 to 4 are unchanged;
  validation 3 to 2 reflects incomplete negative-case coverage; observable
  functional tests 4 to 6 and platform matrix 2 to 3 reflect Podman plus
  manual Rocky 9/10 KVM evidence, not KVM CI enforcement; lifecycle/guardrails
  2 to 2 remain partial. CI 0.5 to 0.5 reflects configured checks without a
  result at this uncommitted ref, not a verified passing required CI run.
- **Docs:** operator docs 4 to 2 and metadata 2 to 1 reflect the conflicting
  Ansible minimum and incomplete compatibility/release detail;
  test/limitations 1 to 2 reflect the updated coverage and gap matrix;
  contribution contract 2 to 2 is unchanged.

**Total: 69.5/100 (rounded down to 69%); score-based and final state: Beta.**
The role supports only Rocky Linux 9 and 10, not RHEL. Check/diff coverage,
some transitions and interruption recovery, a consistent compatibility
contract, and required CI evidence at the assessed ref remain RC blockers.
The smallest readiness gains are to reconcile the Ansible minimum, test
check/diff and missing transitions, strengthen destructive ownership checks,
and verify required CI at a committed ref. See [TESTING.md](TESTING.md) for
runtime and coverage boundaries. No production-readiness review is recorded.

## Compatibility and releases

The `iac_blueprint.dovecot` fields and public state names are the compatibility
contract. Additive changes are preferred; removals or changed meanings require
a migration note and a major-version release. Releases are published as Git
tags; this repository does not currently guarantee a release cadence or a
separately maintained compatibility matrix. See `meta/main.yml` for the
Ansible Galaxy role metadata and declared platform family.

**COPYRIGHT** 2026 ^(ida|arsi)$ collective  
**LICENSE** MIT License [LICENSE](LICENSE)  
**AUTHORS**
- Arsi Atomi <arsi@atomi.sh>  
- Arsi Atomi <arsi.atomi@valtori.fi>  

Overview
========

This Ansible role provides a declarative way to install and manage Dovecot on
Rocky Linux systems. It manages the Dovecot package and service lifecycle,
generates the main service configuration, and can maintain supporting host
resources such as directories, files, bind mounts, cron jobs, and Git working
trees.

The role uses the `iac_blueprint` model to keep the desired Dovecot state in a
structured inventory while Ansible applies the host-specific implementation.
The Dovecot service configuration supports IMAP and POP3 protocols, mail
location, authentication mechanisms, plaintext authentication policy, TLS
settings, and additional Dovecot parameters.

The role is intended for repeatable installation and configuration of Dovecot
hosts. State-specific operations allow operators to install or remove the
package, update configuration, and control the service without having to
reimplement the underlying Ansible task flow.

Supported target operating systems:

- Rocky Linux 9 and 10

Supporting host resources are implemented through the shared task library
included under `tasks/shared`. This keeps common filesystem, bind, cron, Git,
and task-report behavior consistent with other Engine-managed roles.

Security behavior
-----------------

The role rejects `extra_parameters` that overlap security-managed settings and
rejects newline injection in configuration values. Dovecot configuration is
rendered as a restrictive candidate, validated against a staged copy of the
configuration tree, and installed only after validation; validation or
replacement failures leave the live file untouched. Includes that use absolute
paths outside the staged tree retain a live-tree dependency. If such a
dependency is unavailable, validation fails closed and the live file is not
replaced. Dovecot
2.4 uses `auth_allow_cleartext = no` when plaintext authentication is disabled.
Depending on the Rocky package version and included modules, effective
`doveconf` output may expose only a supported subset of requested protocols or
authentication mechanisms. The role preserves requested values in its managed
file and requires effective IMAP, plain authentication, and the configured
plaintext/TLS security policy.
Managed changes notify a reload handler when the service is running. At the
start of a convergence that may reload Dovecot, exactly one immutable pre-run
configuration snapshot is created when a managed configuration already exists.
Snapshot and marker creation has guarded cleanup for partial creation. If reload
fails, the role restores that role-owned snapshot and reloads it before reporting
failure. Configuration rollback is ownership-checked again immediately before
overwrite/removal and fails closed if a symlink, marker, checksum, or ownership
race is detected. The default Molecule scenario exercises the normal rollback
path; focused local guard tests cover changed-live, changed-snapshot,
marker-replacement, and cleanup-race protections. They do not simulate a
concurrent OS-level writer.

This is deliberately **not a full host-resource transaction**. Filesystem, Git,
cron, bind, and service operations are not rolled back as a group after a later
resource failure; the role leaves those changes in place and reports the failure.
This avoids deleting or overwriting pre-existing or unmanaged resources. Operators
must inspect those resources after a failed `present` run and rerun convergence.
Cron and destructive cleanup have their own ownership markers and repeated checks;
bind migration restores the service state, but concurrent mount/fstab changes remain
a residual risk. The role does not claim atomic rollback across these resources.
Inventory validation and a temporary configuration render happen before package
bootstrap. Effective `doveconf` validation cannot run until the Dovecot package
exists; on a new host, installing that package is the unavoidable bootstrap
residual. The installed configuration is still rendered and validated before
it replaces or creates the managed file, and before shared resources converge.
Candidate, previous, and managed configuration cleanup requires a root-owned
`0600` role-managed marker; unowned regular files are preserved and cleanup
fails closed. Resource
removal is guarded in every state, and bind removal fails closed unless
structured `findmnt` and `/etc/fstab` ownership checks agree. Migration
quiesces the service and never lazy-unmounts.

The generated managed configuration and task report use mode `0600`. Arbitrary
`extra_parameters` values are deliberately not classified as secret or
non-secret; operators must treat the generated configuration as sensitive.
Managed filesystem records retain their explicitly requested mode, so callers
must set a restrictive mode for secret-bearing files (for example `0600`). The
role cannot safely infer which arbitrary shared-resource files contain private
keys, so this remains a caller responsibility and residual risk.

These operational states are supported:

| State | Operation | Documentation |
| --- | --- | --- |
| `validate` | Validate inventory only | [validate](docs/states/validate.md) |
| `install` | Install and configure Dovecot | [install](docs/states/install.md) |
| `uninstall` | Uninstall Dovecot and managed resources | [uninstall](docs/states/uninstall.md) |
| `present` | Ensure package and declared resources/configuration are present | [present](docs/states/present.md) |
| `absent` | Remove package and declared managed resources/configuration | [absent](docs/states/absent.md) |
| `configuration_present` | Converge Dovecot configuration only | [configuration_present](docs/states/configuration_present.md) |
| `started` | Start and enable the service | [started](docs/states/started.md) |
| `stopped` | Stop and disable the service, if installed | [stopped](docs/states/stopped.md) |
| `restarted` | Restart and enable the service | [restarted](docs/states/restarted.md) |

The shared filesystem, bind, cron, and Git operations are resource effects of
`present` and `absent`, not additional top-level public states. The dispatcher
contains exactly the nine states listed above; no additional public operational
states are implemented.

An explicit state is required; the role does not assume a destructive or
installing action when `state` is omitted. The `validate` state validates the
complete blueprint and performs no host-state changes. TLS `ssl_cert` and
`ssl_key` must be supplied together as absolute paths whenever `ssl` is `yes`
or `required`.
The generated configuration remains under the fixed `/etc/dovecot/conf.d`
tree; configuration-directory overrides are rejected. Destructive resource
declarations must use specific paths, not broad trees such as
`/etc/dovecot/conf.d` or `/var/lib/dovecot`.

Requirements
------------

- Operating system
  - Rocky Linux 9
  - Rocky Linux 10

- Automated test coverage
  - The current Molecule matrix and scenario coverage are documented in
    [TESTING.md](TESTING.md).

- Other components
  - Ansible 2.15 or higher

Configuration
-------------

Role data is read from `iac_blueprint.dovecot`.

Minimal runnable example
------------------------

The following example is self-contained for installing Dovecot and managing
its basic configuration. It uses the system-user mail location and does not
require virtual-mail users, domains, certificates, or an external repository.
The `ssl: "no"` setting is suitable only for a local test; production hosts
should configure TLS certificates and require encrypted connections.

```yaml
iac_blueprint:
  dovecot:
    configuration:
      protocols:
        - "imap"
        - "pop3"
      mail_location: "maildir:~/Maildir"
      auth_mechanisms:
        - "plain"
        - "login"
      disable_plaintext_auth: true
      ssl: "no"
```

Use it with a playbook such as:

```yaml
---
- name: "Install Dovecot"
  hosts: mail_servers
  become: true
  roles:
    - role: ansible-iac-role-dovecot
      state: install
```

Shared host resources
---------------------

The role can manage Dovecot-related host resources through the shared task
library under `tasks/shared`. Add these optional fields under
`iac_blueprint.dovecot`:

- `directories` maps to `iac_fs_directories`
- `files` maps to `iac_fs_files`
- `binds` maps to `iac_fs_binds`
- `cron` maps to `iac_cron`
- `git` maps to `iac_git_repos`

The role API is `iac_blueprint.dovecot.cron`; `iac_cron` is only the internal
variable passed to the shared task wrappers.

Shared host resource example
----------------------------

```yaml
iac_blueprint:
  dovecot:
    configuration:
      mail_location: "maildir:~/Maildir"
    directories:
      - path: /srv/dovecot-data
        owner: root
        group: root
        mode: "0750"
    files:
      - path: /etc/dovecot/conf.d/99-local-extra.conf
        content: |
          mail_max_user_connections = 20
        owner: root
        group: root
        mode: "0644"
    binds:
      - source: /srv/dovecot-data
        target: /var/lib/dovecot-data
        owner: root
        group: root
        mode: "0750"
        move_from_target: false
    cron:
      - name: dovecot-mail-check
        user: root
        minute: "*/15"
        job: "/usr/local/bin/dovecot-mail-check"
        cron_file: dovecot-mail-check
    git:
      - repo: https://github.com/example/dovecot-config.git
        dest: /srv/dovecot-config
        version: main
        single_branch: true
```

The directory, file, bind, and cron records above are usable as written. The
Git URL is a placeholder and must be replaced with an accessible repository
before that entry is enabled. Bind records manage host storage and are not
automatically connected to Dovecot's mail location unless the configured
`mail_location` points to the bind target.

Cron record state is evaluated independently for each record. If `state` is
omitted or set to `present`, the record is ensured by the present/install
states and requires a `job`. If `state` is `absent`, the record is removed by
removing the role-managed whole file `/etc/cron.d/<cron_file>`; it does not
require a `job` and leaves the `cronie` package state unchanged. This
whole-file removal is intentional: a cron file
named by an explicit absent record is owned by this role. `cron_file` is a
validated basename and cannot select an arbitrary path. For example:

```yaml
iac_blueprint:
  dovecot:
    cron:
      - name: "dovecot-mail-check"
        state: "absent"
        cron_file: "dovecot-mail-check"
```

The global `absent` and `uninstall` states retain the legacy shared-task
entry-removal behavior for records without an explicit record `state`.
Present/install management writes a restrictive sidecar manifest only when it
creates the cron file, and refreshes an already valid role-owned manifest after
subsequent changes. It never claims ownership of a pre-existing unmarked cron
file. Explicit absent removal requires an intact root-owned `0600` manifest
whose recorded inode, checksum, and size still match the file immediately
before removal; otherwise the role fails closed. If both file and manifest are
absent, explicit absent is a successful no-op. A valid stale manifest with no
file is removed safely; malformed, mismatched, or insecure markers fail closed.
The manifest is removed together with the owned cron file. The final checks
reduce, but cannot eliminate, races with another process changing the files
between validation and deletion.

Virtual-mail example
--------------------

For virtual mail, `%d` and `%n` are Dovecot runtime placeholders for the login
domain and username. For example, `user@example.org` resolves to the
`/var/vmail/example.org/user` path under the bind-mounted storage:

```yaml
iac_blueprint:
  dovecot:
    configuration:
      mail_location: "maildir:/var/vmail/%d/%n"
    directories:
      - path: /srv/mail
        owner: vmail
        group: mail
        mode: "0750"
    binds:
      - source: /srv/mail
        target: /var/vmail
        owner: vmail
        group: mail
        mode: "0750"
        move_from_target: true
```

This virtual-mail example requires the `vmail` operating system user and
group, mail domains, mail users, and authentication `passdb`/`userdb` records
to already exist or to be managed by the surrounding mail-server
configuration. The Dovecot role does not create those objects.

The shared host-resource integration is documented in the next section. The
exact record formats are documented in the shared task README at
`tasks/shared/README.md`. Bind records use `source` as the real storage path
and `target` as the path kept available through the bind mount. With
`move_from_target: true`, existing target contents are moved to an empty
source directory before the first mount. The task fails instead of merging
two non-empty directories automatically.

The `present` and `install` flows create the declared resources before the
Dovecot service is started. The `absent` and `uninstall` flows stop Dovecot,
remove the declared resources, unmount declared binds, and remove the Dovecot
package. Bind-backed data is not purged by default. Set
`purge_on_absent: true` explicitly on a bind record only when deleting its
role-managed source data is intended; broad paths such as `/etc/dovecot` and
`/var/lib` are rejected by preflight validation. Purge sources that are
symlinks are also refused so cleanup cannot follow a link outside the declared
scope. Before bind removal, the role verifies that any live mount and fstab
entry match the declared source and target; unrelated mounts are refused. The
symlink check is repeated immediately before removal, but without an ownership
manifest no filesystem check can provide a race-proof guarantee against a
concurrent administrator changing the source after validation.

Migration and compatibility
---------------------------

Older inventories that relied on removal implicitly purging bind data must add
`purge_on_absent: true` to each bind record where that deletion is intentional.
Existing inventories using the normal `/etc/dovecot` and
`/etc/dovecot/conf.d` defaults remain compatible. Custom configuration-tree
overrides must be migrated back to that fixed tree: they are rejected because
the role has no ownership manifest for safely proving that an arbitrary path
belongs to Dovecot before configuration or cleanup.

The shared filesystem helpers support inline files, controller-side or
target-side file copies, directory ownership and modes, optional SELinux
contexts, bind mounts, cron jobs, and Git working trees. They use the common
`iac_*` variables internally while the Dovecot blueprint keeps the service
specific configuration under `dovecot`.

Repository checkout
-------------------

The shared task library is included as a Git submodule under `tasks/shared`.

The checked-in submodule is initialized at the pinned commit `d70d58e`.
Clean checkouts made without submodules need
`git submodule update --init --recursive`; the role does not silently vendor or
replace the external dependency.
Clone the repository with submodules:

```bash
git clone --recurse-submodules https://github.com/idarsi/ansible-iac-role-dovecot.git
```

If the repository was already cloned without submodules, initialize them with:

```bash
git submodule update --init --recursive
```

Testing
-------

The `podman-default` and `podman-rocky10` Molecule scenarios cover Dovecot installation and
configuration, shared filesystem resources, bind migration, cron jobs, and a
local Git checkout on Rocky Linux 9 and 10. See [TESTING.md](TESTING.md) for
the complete scenario coverage, current limitations, and test commands.

Code Quality
------------

This project follows the Engine Ansible role coding standard.
