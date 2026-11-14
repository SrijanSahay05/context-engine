import subprocess
import sys
from pathlib import Path


def test_entrypoint_runs() -> None:
    entrypoint = Path(__file__).resolve().parents[1] / "main.py"
    result = subprocess.run(
        [sys.executable, str(entrypoint)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "Hello from context-engine!"
