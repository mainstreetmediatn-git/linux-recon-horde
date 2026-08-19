from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_instruction_documents_are_not_distributed_as_python_packages():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    discovery = config["tool"]["setuptools"]["packages"]["find"]

    assert "horde*" in discovery["include"]
    assert "instructions*" in discovery["exclude"]


def test_operating_rules_protect_the_cli_without_editing_it():
    rules = (ROOT / "instructions" / "OPERATING_RULES.md").read_text()

    assert "`horde/cli.py` is frozen." in rules
    assert "Only modify it after explicit human instruction naming that file." in rules
