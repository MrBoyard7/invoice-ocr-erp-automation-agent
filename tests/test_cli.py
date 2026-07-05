"""Tests for the command-line interface."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from invoice_automation.cli import main


@pytest.fixture()
def cli_runner() -> CliRunner:
    return CliRunner()


def test_validate_ncf_command_accepts_valid_value(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(main, ["validate-ncf", "B0100000001"])
    assert result.exit_code == 0
    assert "valid NCF" in result.output


def test_validate_ncf_command_rejects_invalid_value(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(main, ["validate-ncf", "not-an-ncf"])
    assert result.exit_code == 1
    assert "Invalid NCF" in result.output


def test_run_command_completes_with_empty_watch_folder(
    cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SADE_DATABASE_URL", f"sqlite:///{tmp_path / 'cli_demo.db'}")
    monkeypatch.setenv("SCANNER_WATCH_FOLDER", str(tmp_path / "incoming"))
    monkeypatch.setenv("SCANNER_PROCESSED_FOLDER", str(tmp_path / "processed"))
    monkeypatch.setenv("ZAPIER_WEBHOOK_URL", "")

    result = cli_runner.invoke(main, ["run", "--invoice-type", "accounts_payable"])

    assert result.exit_code == 0
    assert "Processed: 0 | Failed: 0" in result.output
