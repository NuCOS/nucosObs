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

### Changed

- Made pytest the primary test runner and added development test dependencies.
- Declared Python 3.8+ and `websockets>=15` support consistently in packaging,
	requirements, README, and the helper script.

### Tests

- Expanded pytest coverage from 13 to 22 tests with regression and loopback
	integration coverage for repaired behavior.
- Added loopback coverage for websocket authentication, routed messages, and
	final-client cleanup with the fallback token path forced.
