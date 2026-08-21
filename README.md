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
package. Bind-backed data is purged during removal, so review
`purge_on_absent` behavior and backups before using a destructive state.

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
