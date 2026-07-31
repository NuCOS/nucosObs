## Unreleased - 2026-07-31

### Fixed

- Restored executor dispatch and callback completion for `@inThread` observer
	handlers.
- Restored sequential async observer delivery so shutdown cannot overtake an
	active handler.
- Added support for the current `websockets` server API and fixed its closed
	connection lifecycle.
- Repaired aiohttp client startup, websocket cleanup, callback defaults, and
	client-session shutdown.
- Corrected runtime loop binding across observers, observables, interfaces, and
	`main_loop()`.
- Generated JSON-safe fallback websocket identifiers and nonces when `nucosCR`
	is unavailable.
- Released standard websocket nonce and authentication state when authentication
	is rejected or a client disconnects.
- Made aiohttp websocket removal idempotent, clean timeout state before the
	close handshake, and preserve cleanup when optional callbacks fail.

### Changed

- Made pytest the primary test runner and added development test dependencies.
- Declared Python 3.11+ and `websockets>=15` support consistently in packaging,
  requirements, and README.
- Added `Runtime` for applications that need isolated event loops, observer
	registries, observable registries, debug state, and thread pools in one
	process.
- Modernized package metadata with `pyproject.toml`, build-system metadata,
	Markdown project descriptions, dependency bounds, and test extras.
- Raised the supported Python baseline to 3.11+ to use modern asyncio and the
	current pytest toolchain without legacy compatibility branches.
- Removed obsolete Python-version queue handling now that `asyncio.Queue()` is
	the sole supported queue construction path.
- Added a GitHub Actions pytest matrix for Python 3.11 through 3.13 with JUnit
	output and wheel-build validation.
- Documented event payloads, sequential delivery, threaded handlers, isolated
	runtimes, websocket authentication, and supported test workflows in README.
- Added open-source repository health documentation, GitHub issue and pull
	request templates, dependency updates, and source distribution metadata.
- Added a coverage-grounded final readiness screen with non-breaking proposals
	for logic coverage and developer usability.
- Made `StdinInterface` testable with optional input-stream and loop injection;
	stdin remains the default for existing callers.
- Made `TwoWayInterface` preserve caller directives, parse full delay values,
	and report stop state consistently.

### Removed

- Removed the obsolete `genie.sh` virtualenv/nose2 helper and `aftermath.py`
	JUnit XML post-processor; CI now provides pytest JUnit output and wheel builds.

### Tests

- Expanded pytest coverage from 13 to 22 tests with regression and loopback
	integration coverage for repaired behavior.
- Added loopback coverage for websocket authentication, routed messages, and
	final-client cleanup with the fallback token path forced.
- Added standard websocket authentication-rejection coverage, including normal
	close handling and complete server-state cleanup.
- Added aiohttp loopback coverage for accepted and rejected authentication,
	connection replacement, receive timeouts, and failing close callbacks.
- Added regression coverage that a failing `closeSanely` callback still removes
	the replaced aiohttp connection.
- Added a runtime-isolation test that runs two applications through separate
	`Runtime.main_loop()` instances.
- Built the distribution wheel successfully with the configured build backend.
- Added focused async tests for stdin commands, multi-digit leave delays,
  targeted two-way routing, broadcast routing, waits, and stop behavior.
