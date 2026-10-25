# `install` state

Runs `present` and then ensures the Dovecot service is started and enabled.
`present` installs the Dovecot package, validates and converges configuration,
and applies declared filesystem, bind, Git, and cron resources. Cron records
explicitly set to `absent` are removed. Optional `cronie` and `git` packages are
installed when applicable resources are declared.

Configuration is transactionally validated and may be rolled back if
configuration reload or resource convergence fails. This is not an atomic
transaction for host resources: resource changes are not generally rolled back.
See the [README security and transaction notes](../../README.md#security-behavior).
