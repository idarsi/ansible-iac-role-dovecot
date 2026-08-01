ANSIBLE-IAC-ROLE-DOVECOT
========================
**COPYRIGHT** 2026 ^(ida|arsi)$ collective  
**LICENSE** MIT License [LICENSE](LICENSE)  
**AUTHORS**
- Arsi Atomi <arsi@atomi.sh>  
- Arsi Atomi <arsi.atomi@valtori.fi>  

Overview
========

This Ansible role installs and configures Dovecot on RHEL-compatible systems.
It supports IMAP and POP3 service configuration, mail location, authentication
mechanisms, plaintext authentication policy, and optional TLS certificate paths.

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

Requirements
------------

- Operating system
  - Red Hat Enterprise Linux 9
  - Red Hat Enterprise Linux 10
  - Rocky Linux 9
  - Rocky Linux 10

- Other components
  - Ansible 2.15 or higher

Configuration
-------------

Role data is read from `iac_blueprint.dovecot`.

Example:

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
      ssl_cert: "/etc/pki/dovecot/certs/dovecot.pem"
      ssl_key: "/etc/pki/dovecot/private/dovecot.pem"
```

Code Quality
------------

This project follows the Engine Ansible role coding standard.
