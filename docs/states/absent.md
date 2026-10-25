# `absent` state

Stops and disables Dovecot, removes managed configuration and its candidate,
previous-snapshot and ownership-marker artifacts, then removes the declared
cron, Git, bind and filesystem resources and the Dovecot package. Cleanup
requires valid ownership/scope checks; unmanaged configuration is not silently
deleted. This is not `all_absent`: no such broad-remnant state is implemented.
Auxiliary `cronie` and `git` packages are not removed.
