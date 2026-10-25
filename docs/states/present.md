# `present` state

Ensures the Dovecot package is installed, renders and validates the managed
configuration, and converges declared supporting resources: filesystem entries,
bind mounts, Git working trees, and cron jobs. Cron entries explicitly
requested absent are removed; omitted or non-absent entries are ensured
present. It installs `cronie` or `git` when corresponding present records need
them.

This state does not start or enable the service. Configuration reloads when
needed if the service is running. Configuration can be rolled back on a
subsequent failure, but the entire host-resource set is not transactional.
