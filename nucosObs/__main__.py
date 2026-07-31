"""Command-line diagnostics for nucosObs installations."""

import argparse
import json
import platform
from importlib import metadata

import nucosObs
from nucosObs.version import version


def _dependency_version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def diagnostics():
    """Return the installed package and default runtime diagnostic state."""
    return {
        "package": "nucosObs",
        "version": version,
        "python": {
            "installed": platform.python_version(),
            "supported": ">=3.11",
        },
        "dependencies": {
            "aiohttp": _dependency_version("aiohttp"),
            "websockets": _dependency_version("websockets"),
        },
        "runtime": {
            "debug_enabled": bool(nucosObs.debug[-1]),
            "loop_closed": nucosObs.loop.is_closed(),
            "observables": len(nucosObs.allObservables),
            "observers": len(nucosObs.allObs),
        },
    }


def main():
    """Print package diagnostics for support and development workflows."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()
    report = diagnostics()
    if args.json:
        print(json.dumps(report, sort_keys=True))
        return

    print(f"{report['package']} {report['version']}")
    print(
        "Python: "
        f"{report['python']['installed']} "
        f"(supported {report['python']['supported']})"
    )
    print(
        "Dependencies: "
        f"aiohttp {report['dependencies']['aiohttp']}, "
        f"websockets {report['dependencies']['websockets']}"
    )
    print(
        "Runtime: "
        f"observers={report['runtime']['observers']}, "
        f"observables={report['runtime']['observables']}, "
        f"loop_closed={report['runtime']['loop_closed']}, "
        f"debug_enabled={report['runtime']['debug_enabled']}"
    )


if __name__ == "__main__":
    main()