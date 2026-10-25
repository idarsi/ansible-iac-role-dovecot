# `configuration_present` state

Renders and validates the managed Dovecot configuration and installs it using
the guarded configuration transaction. A running service is reloaded as needed
after configuration commit. This state does not install the package, converge
declared filesystem/Git/cron/bind resources, or ensure the service is started.
The installed Dovecot tooling is required for effective configuration checks.
