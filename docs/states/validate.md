# `validate` state

Validates the Dovecot blueprint and state-specific destructive bind-removal
inputs, then reports success. For bind records with `purge_on_absent: true`, it
also inspects the target source paths and their path components to reject
symlinks; this is a bounded, read-only target-path check and does not mutate
them. It does not otherwise inspect host runtime state or perform
state-dispatch changes. The common preflight still checks supported OS,
blueprint context and structure before validating values.

Use `state: validate` to check inventory without installing or removing Dovecot.
