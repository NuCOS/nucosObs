# nucosObs

[![PyPI version](https://img.shields.io/pypi/v/nucosObs.svg)](https://pypi.org/project/nucosObs/)
[![Tests](https://github.com/NuCOS/nucosObs/actions/workflows/tests.yml/badge.svg)](https://github.com/NuCOS/nucosObs/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)

`nucosObs` is an observer-observable framework based on `asyncio`.

## Status

The project supports Python 3.11 through 3.13. Continuous integration runs the
full pytest suite and builds a wheel for each supported version.

## Install
```
pip install nucosObs
```


## Documentation
The project ships a small but handy toolbox to build applications using
the observer/observable pattern with ``asyncio``.  It contains helper
classes for observers, observables and a couple of interfaces (stdin,
websockets and aiohttp based websockets) to communicate with running
tasks.

### Example

```python
import asyncio as aio

from nucosObs import main_loop
from nucosObs.observable import Observable
from nucosObs.observer import Observer


class HelloObserver(Observer):
    async def say(self):
        print("Hello")


A = Observable()
O = HelloObserver("O", A)
aio.ensure_future(A.put({"name": "say"}))
main_loop([])
```

See the ``examples`` directory for more advanced usage.

## Event Model

An observable delivers each event to every registered observer queue. Events
can be dictionaries or command strings. Dictionary events use this shape:

```python
{"name": "method_name", "args": ["first argument", "second argument"]}
```

Observers process regular async handlers sequentially. A
`{"action": "stop_observer"}` event stops an observer after its active handler
has completed.

## Threaded Handlers

Use `@inThread()` for synchronous work that must not block the event loop. The
handler runs in the runtime's thread pool. With `callback=True`, register an
async callback for the bound handler in `observer.callbacks`; it runs after the
threaded method finishes.

```python
from nucosObs.observer import Observer, inThread


class Worker(Observer):
    @inThread()
    def calculate(self, value):
        return value * 2
```

## Isolated Runtimes

The module-level `main_loop()` API remains available for existing programs. For
multiple applications in one process, create a `Runtime` and pass it to each
observable and observer. Each runtime owns its event loop, registries, debug
state, and thread pool.

```python
from nucosObs import Runtime
from nucosObs.observable import Observable
from nucosObs.observer import Observer


runtime = Runtime()
events = Observable(runtime=runtime)
worker = Worker("worker", events, runtime=runtime)
runtime.loop.create_task(events.put({"name": "calculate", "args": [21]}))
runtime.loop.create_task(events.put({"action": "stop_observer"}))
runtime.main_loop([])
runtime.close()
```

## Websocket Authentication

Both websocket interfaces send an authentication challenge when `doAuth=True`.
The configured authenticator must provide an async
`startAuth(message, websocket, nonce)` method and return
`(connection_id, user)`. Returning a matching connection ID accepts the client;
returning `None` rejects and closes it. Clients may send regular broker messages
only after successful authentication.

## License

Distributed under the [MIT License](LICENSE.txt).

## Platforms
No specific platform dependency. Python 3.11 or later is required.

## Testing
Install development dependencies with `pip install -r requirements-dev.txt`,
then run the test suite with `python -m pytest`.

The repository runs this command in GitHub Actions on Python 3.11 through 3.13.

For a coverage-grounded view of current readiness and compatible next steps,
see [docs/FINAL_READINESS.md](docs/FINAL_READINESS.md).

## Contributing and Support

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community expectations. Report
security vulnerabilities according to [SECURITY.md](SECURITY.md); for general
questions or reproducible bugs, open a GitHub issue.


