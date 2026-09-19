"""Dependency-free checks for transactional rollback guardrails."""

from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_live_rollback_rechecks_regular_owned_config_and_marker():
    source = (ROOT / "tasks/configuration_transaction_rollback.yml").read_text()
    assert source.count("ansible.builtin.stat:") >= 3
    assert source.count("follow: false") >= 3
    for field in ("isreg", "uid", "gid", "mode", "checksum"):
        assert field in source


def test_changed_live_config_refuses_resource_failure_rollback():
    source = (ROOT / "tasks/configuration_transaction_rollback.yml").read_text()
    assert "dovecot_transaction_expected_config_checksum is defined" in source
    assert (
        "dovecot_rollback_live_config_stat.stat.checksum == "
        "dovecot_transaction_expected_config_checksum"
    ) in source
    assert "dovecot_idarsi_marker_content" in source


def test_changed_previous_and_marker_are_checked_before_restore():
    source = (ROOT / "tasks/reload_transaction_operation.yml").read_text()
    assert "snapshot immediately before restore" in source
    assert "dovecot_previous_config_checksum" in source
    assert "dovecot_previous_marker_checksum" in source
    assert "dovecot_reload_snapshot_marker_content" in source


def test_cleanup_uses_marker_identity_and_final_race_recheck():
    source = (ROOT / "tasks/configuration_transaction_cleanup_record.yml").read_text()
    assert "follow: false" in source
    assert "checksum" in source
    assert "after marker removal" in source
    assert "dovecot_idarsi_marker_content" in source


def test_previous_artifacts_are_not_removed_with_un_guarded_file_tasks():
    for path in (
        "tasks/configuration_transaction_rollback.yml",
        "tasks/reload_transaction_operation.yml",
    ):
        source = (ROOT / path).read_text()
        assert 'path: "{{ dovecot_previous_config_path }}"' not in source


if __name__ == "__main__":
    for test in (
        test_live_rollback_rechecks_regular_owned_config_and_marker,
        test_changed_live_config_refuses_resource_failure_rollback,
        test_changed_previous_and_marker_are_checked_before_restore,
        test_cleanup_uses_marker_identity_and_final_race_recheck,
        test_previous_artifacts_are_not_removed_with_un_guarded_file_tasks,
    ):
        test()
    print("transaction guard checks passed")
