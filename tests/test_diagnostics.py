import json
import subprocess
import sys

import nucosObs


def test_module_diagnostics_prints_stable_human_summary():
    result = subprocess.run(
        [sys.executable, "-m", "nucosObs"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert f"nucosObs {nucosObs.__version__}" in result.stdout
    assert "Python:" in result.stdout
    assert "Runtime:" in result.stdout


def test_module_diagnostics_json_is_machine_readable():
    result = subprocess.run(
        [sys.executable, "-m", "nucosObs", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    diagnostics = json.loads(result.stdout)

    assert diagnostics["package"] == "nucosObs"
    assert diagnostics["version"] == nucosObs.__version__
    assert diagnostics["python"]["supported"] == ">=3.11"
    assert set(diagnostics["dependencies"]) == {"aiohttp", "websockets"}
    assert set(diagnostics["runtime"]) == {
        "debug_enabled",
        "loop_closed",
        "observables",
        "observers",
    }