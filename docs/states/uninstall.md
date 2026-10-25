# `uninstall` state

Dispatches to `absent`. It stops and disables Dovecot, removes its owned
configuration and transaction artifacts, declared cron jobs, Git working
trees, bind mounts and filesystem resources, then removes the Dovecot package.
Removal is limited to declared/managed scopes and guarded by ownership checks;
it does not claim cleanup of arbitrary role-related remnants. Optional
`cronie` and `git` packages are not removed by this workflow.
