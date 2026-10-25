# `stopped` state

Collects service facts and, when the Dovecot service exists, stops it and
disables it at boot. If the service is not installed, the service operation is
skipped. It does not remove the package, configuration, or supporting resources.
