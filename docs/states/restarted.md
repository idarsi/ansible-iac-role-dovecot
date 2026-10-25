# `restarted` state

Requests a systemd restart of the Dovecot service and ensures it is enabled at
boot. It does not install the package, converge configuration, or manage
supporting resources; the service must be available for the restart operation.
