ANSIBLE-IAC-ROLE-DOVECOT
========================
**COPYRIGHT** 2026 ^(ida|arsi)$ collective  
**LICENSE** MIT License [LICENSE](LICENSE)  
**AUTHORS**
- Arsi Atomi <arsi@atomi.sh>  
- Arsi Atomi <arsi.atomi@valtori.fi>  

Overview
========

This Ansible role provides a declarative way to install and manage Dovecot on
RHEL-compatible systems. It manages the Dovecot package and service lifecycle,
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

- Red Hat Enterprise Linux 9 and 10
- Rocky Linux 9 and 10

Supporting host resources are implemented through the shared task library
included under `tasks/shared`. This keeps common filesystem, bind, cron, Git,
and task-report behavior consistent with other Engine-managed roles.

These operations are supported:

Operation                                   | State                 |
--------------------------------------------|-----------------------|
Validate inventory only                      | validate              |
Installing and configuring Dovecot          | install               |
Uninstalling Dovecot                        | uninstall             |
Installing and configuring Dovecot package  | present               |
Uninstalling Dovecot package                | absent                |
Updating Dovecot configuration              | configuration_present |
Starting Dovecot                            | started               |
Stopping Dovecot                            | stopped               |
Restarting Dovecot                          | restarted             |
Managing shared filesystem resources        | present / absent      |
Managing shared bind mounts                 | present / absent      |
Managing shared cron jobs                   | present / absent      |
Managing shared Git working trees           | present / absent      |

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
  - Red Hat Enterprise Linux 9
  - Red Hat Enterprise Linux 10
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

The `default` and `rocky10` Molecule scenarios cover Dovecot installation and
configuration, shared filesystem resources, bind migration, cron jobs, and a
local Git checkout on Rocky Linux 9 and 10. See [TESTING.md](TESTING.md) for
the complete scenario coverage, current limitations, and test commands.

Code Quality
------------

This project follows the Engine Ansible role coding standard.
