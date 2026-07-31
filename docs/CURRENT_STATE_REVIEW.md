# nucosObs Current State Review

### PHASE 1 IN PROGRESS: Repository Baseline and Compatibility Recovery

**Status**: P0/P1 REMEDIATION COMPLETE; FOLLOW-UP LIFECYCLE WORK REMAINS
**Date**: July 31, 2026
**Scope**: Current `master` at `0521e76` (`0.4.17`), including the merge of
local commit `e1942ea` and upstream compatibility/test work.

## Executive Summary

`nucosObs` is a compact asyncio observer/observable toolkit with stdin,
websocket, aiohttp-websocket, and observable-to-observable interfaces. The
core idea remains clear: an `Observable` fans an event out to observer queues,
and each `Observer` dispatches the event to a named handler.

The latest merge includes useful work: package version exposure, removal of
deprecated `asyncio.Queue(loop=...)` usage in two interfaces, an aiohttp
heartbeat option, and an initial unittest suite. It also combines incompatible
assumptions about event-loop ownership and current websocket APIs. Several
public paths are presently broken or unsafe, including the documented
`inThread` decorator and the basic `websockets` server when installed with the
current unpinned dependency version. Those release-blocking issues have now
been repaired and are covered by focused pytest regression tests.

The source tree passes a syntax smoke check with Python 3.13.5. This does not
exercise websocket connections, thread-backed observers, shutdown callbacks,
or package installation.

> **Testing Suite Update**
>
> Pytest is now the designated primary test runner. Run `python -m pytest`
> from the repository root; the existing unittest-based tests remain
> collectable during the migration. Test dependencies are declared in
> `requirements-dev.txt` (`pytest` and `pytest-asyncio`).
>
> Each repair ships with regression coverage for its failure mode. The suite
> now covers `inThread` handlers and callbacks, thread-pool reuse, current
> websocket server compatibility, aiohttp client startup, closed-connection
> cleanup, callback defaults, observer delivery ordering, and current-loop
> binding. Prefer local loopback integration tests for interface behavior; use
> fakes only at external boundaries.

## Repository Snapshot

| Area | Current state |
| --- | --- |
| Package version | `0.4.17` in `nucosObs/version.py`; exposed as `nucosObs.__version__` |
| Runtime model | Module-global event loop, observer registry, observable registry, debug flag, and thread pool |
| Core dispatch | `Observable.put()` copies an event to every registered queue; `Observer.observe()` parses and invokes named handlers |
| Interfaces | `StdinInterface`, `TwoWayInterface`, `WebsocketInterface`, and `AiohttpWebsocketInterface` |
| Dependency declaration | `setup.py` declares `websockets` and `aiohttp`; `requirements.txt` duplicates them without versions |
| Test suite | 22 tests collected by pytest, including 9 new regression and loopback integration tests |
| Documentation | README offers a minimal example; this review is the first maintained technical-state document |

## Recent History Assessment

`0521e76` is a merge of local `e1942ea` (`new version`) and upstream history
through `51cce0a`. The merge itself has no textual conflict markers, but it
brings together a local websocket/lifecycle change with an upstream asyncio
compatibility and test bundle.

Relevant imported work:

- `fef4c4a` creates and installs a default event loop at import time and
  removes deprecated queue loop arguments from stdin and two-way interfaces.
- `754c084` adds the initial test suite.
- `e1942ea` adds aiohttp client indexing and deferred replacement-client
  closure, fixes a syntax error in `observable.py`, bumps the version, and
  changes observer dispatch semantics.

The most serious regression introduced by `e1942ea` was the removal of the
`inThread` branch from `Observer.observe()` while retaining the decorator as a
public API. That regression is now repaired and protected by pytest coverage.

## Findings

### Resolved P0 - `inThread` handlers broken by the latest local change

**Location**: `nucosObs/observer.py`

The `inThread` decorator explicitly supports synchronous, time-consuming
handlers. Before `e1942ea`, `Observer.observe()` submitted those handlers to
the shared `ThreadPoolExecutor`. It now always executes `method(*args)` and
passes its result to `asyncio.ensure_future()`.

A synchronous decorated handler returns an ordinary value, which is not
awaitable; `ensure_future()` therefore raises `TypeError`. The handler also
runs on the event-loop thread before failing, defeating the decorator's
non-blocking purpose. Restore the executor branch and preserve callback
execution after the executor future completes. Add a test with a synchronous
decorated handler plus a callback.

**Resolution**: synchronous decorated methods now run through the current
event loop's executor, their callbacks are awaited, and the shared pool stays
available after `main_loop()` returns.

### Resolved P0 - Default `websockets` installation is incompatible with the server

**Location**: `nucosObs/websocketInterface.py`, `setup.py`, `requirements.txt`

The installed `websockets` 15.0.1 API calls server handlers with one
`ServerConnection` argument. `WebsocketInterface.handler()` requires
`(websocket, path)`, so `websockets.serve()` cannot invoke it. The package has
no upper dependency bound and will install the latest incompatible release.

Choose one supported API deliberately: migrate the interface to the current
`websockets` asyncio API and test it, or pin to the legacy compatible major
version. Record the decision in `python_requires`, classifiers, and the
README.

**Resolution**: the server now accepts the one-argument `websockets` 15
handler contract and uses `ConnectionClosed` rather than the removed `.open`
attribute. Package dependencies now require `websockets>=15`.

### Resolved P1 - aiohttp client mode raises `NameError`

**Location**: `nucosObs/aiohttpWebsocketInterface.py`

`AiohttpWebsocketInterface.connect()` calls `websockets.connect()` but the
module never imports `websockets`. Calling client mode therefore fails before
it attempts a network connection. Import the dependency and cover the client
creation path with a local websocket test or a small fake.

**Resolution**: client mode now uses `aiohttp.ClientSession.ws_connect()` and
closes its session during shutdown. A loopback aiohttp test covers this path.

### Resolved P1 - optional close callback is awaited unconditionally

**Location**: `nucosObs/aiohttpWebsocketInterface.py`

When `closeOnClientQuit=True` and the last connection exits, the listener
executes `await self.onCloseCallback(user)` even when the default
`onCloseCallback` is `None`. This raises `TypeError` during cleanup. Guard the
call and state whether callbacks must be asynchronous. The prior guarded
callback was removed in `e1942ea`.

**Resolution**: callback execution is guarded, while the `client exit` broker
event is still emitted for the final closed connection.

### Resolved P1 - disconnected aiohttp clients remain registered by default

**Location**: `nucosObs/aiohttpWebsocketInterface.py`

`remove_connection()` now runs only inside the `closeOnClientQuit` branch.
With its default value of `False`, closed sockets remain in `ws`, `ids`, and
potentially authentication maps. Broadcasts then repeatedly target dead
sockets, and `send_by_client()` can select stale connection indices. Always
remove a closed connection; keep the optional application-shutdown decision
separate from resource cleanup.

**Resolution**: closed connections are removed regardless of
`closeOnClientQuit`; application shutdown remains optional.

### Resolved P1 - global event-loop references create split-loop behavior

**Location**: `nucosObs/__init__.py`, `nucosObs/observable.py`,
`nucosObs/observer.py`, interfaces

Modules import `loop` directly from `nucosObs`. Reassigning `nucosObs.loop`
later, as the tests do, does not update those imported references. The default
loop created at import time can therefore differ from the loop used by
`main_loop()` or by a caller. This is especially risky for `startSchedule()`
and stdin reader registration.

Make loop ownership explicit. The conservative path is to accept a loop (or
obtain the running loop at execution time) and avoid module-level imported
loop aliases. Until then, tests should not mask the problem by reassigning the
package global after imports.

**Resolution**: newly created observables, observers, stdin interfaces, and
two-way interfaces capture the current `nucosObs.loop`. `main_loop()` also
creates its gather operation inside the configured loop. The registries and
loop remain process-global and are still candidates for a future runtime
object refactor.

### Resolved P1 - supported Python versions are contradictory

**Location**: `README.md`, `setup.py`, `genie.sh`, source files

The README and setup guard state Python 3.5 support, while the package uses
f-strings, which require Python 3.6+, and its asyncio changes target modern
Python. `genie.sh` still creates a Python 3.5 environment. The classifiers
list Python 3.8 through 3.11 but do not declare `python_requires`; the review
smoke check used Python 3.13.5.

Set an intentional minimum version, add `python_requires`, align classifiers,
README, and the helper script, and run the suite on every claimed version.

**Resolution**: Python 3.8 is now the explicit minimum in packaging and the
README; `genie.sh` provisions Python 3.8 and invokes pytest.

### P2 - lifecycle behavior lacks integration coverage

**Location**: `tests/`, `nucosObs/observer.py`, websocket interfaces

The expanded suite now covers basic websocket serving, aiohttp client startup,
closed-connection cleanup, thread-backed handlers, and delivery ordering. It
still omits authentication acceptance/rejection, replacement of an existing
authenticated connection, timeout cleanup, and callback failure propagation.
The global registries and event-loop state are still mutated directly, which
makes test isolation a design concern. Add focused integration tests for the
remaining network paths and move runtime state behind an application object.

**Testing commitment**: use pytest fixtures to reset runtime state and add
one regression test for every defect before or alongside its fix. Add
loopback integration coverage for each supported network interface rather than
only unit-level mocks.

### Resolved P2 - delivery is now fire-and-forget without error reporting

**Location**: `nucosObs/observer.py`

The latest observer change schedules every handler with `ensure_future()` and
does not retain or inspect the task. Handler exceptions are not delivered to
the caller, ordering is no longer serialized, and shutdown can finish before
handlers complete. This may be intended for concurrency, but it is a behavior
change from awaited delivery and needs an explicit policy: sequential delivery,
tracked concurrent tasks, or a configurable mode with error handling.

**Resolution**: regular asynchronous handlers are awaited sequentially, which
restores the pre-merge shutdown and ordering semantics. Thread-backed handlers
remain asynchronous to the event loop through the executor.

## Improvement Plan

### 1. Expand remaining lifecycle integration coverage

- Add aiohttp authentication success, rejection, replacement, and timeout
  tests using local loopback servers.
- Test close-callback failures and define whether they should propagate or be
  logged while cleanup continues.
- Test WebSocket authentication and server shutdown with multiple clients.
- Keep adding pytest regression and loopback integration tests before marking
  each lifecycle item complete.

**Acceptance criteria**: all supported authentication and disconnect paths are
covered by deterministic local integration tests.

### 2. Make lifecycle ownership explicit

- Replace mutable module-global loop coupling with an application/runtime
  object or dependency-injected loop.
- Give global observer and observable registries a resettable owner rather
  than sharing process-wide mutable lists.
- Define shutdown semantics for observers, scheduled tasks, thread-pool work,
  interfaces, and pending handler tasks.

**Acceptance criteria**: two independent runtime instances can execute in one
process without queue or loop cross-contamination.

### 3. Make packaging reproducible

- Declare `python_requires` and dependency ranges in one authoritative place.
- Remove the obsolete Python 3.5 setup path or update it to the supported
  matrix.
- Replace deprecated packaging fields (`description-file`) and remove unused
  setup-time imports and directory scans where practical.
- Add a CI matrix for the supported Python versions and dependency API line.
- Run `python -m pytest` as the primary CI test command; retain unittest
  collection only while the existing test classes are being migrated.

**Acceptance criteria**: a clean virtual environment installs the package and
runs its smoke suite using the advertised Python and dependency versions.

### 4. Establish user-facing documentation

- Expand the README with a current Python/dependency support statement and a
  correct shutdown example.
- Document event payload formats, observer concurrency, `inThread`, bridge
  hooks, and interface authentication expectations.
- Maintain `docs/CHANGELOG.md` for confirmed user-visible releases only.
- Keep this review updated until the P0 and P1 items are resolved.

## Verification Performed

- Inspected current source, examples, package metadata, tests, and recent
  history through `0521e76`.
- Compared the merge result against both parents and reviewed the substantive
  `e1942ea`, `fef4c4a`, and `754c084` changes.
- Ran `git diff --check`; it reports only a trailing blank line in the newly
  added `tests/test_app.py`.
- Confirmed syntax with `python -m compileall -q nucosObs tests` using active
  Python 3.13.5.
- Established the original pytest baseline with `python -m pytest`: 13 tests
  passed in 0.11 seconds using pytest 9.0.2 and pytest-asyncio 1.3.0.
- After remediation, `python -m pytest` reports 22 passing tests in 0.35
  seconds on Python 3.13.5.
- Inspected installed `websockets` 15.0.1: `serve()` expects a one-argument
  handler, while the package declares a two-argument handler.
- Confirmed that `AiohttpWebsocketInterface.connect()` has no `websockets`
  module in its globals.

No source code was changed as part of this review.