# nucosObs User Documentation

**Version**: 0.4.17  |  **Python**: 3.11+  |  **License**: MIT

`nucosObs` is an observer-observable framework built on Python's `asyncio`. It
provides a clean event-driven architecture for coordinating asynchronous tasks,
with built-in support for websocket communication, scheduling, threaded
execution, and more.

---

## Table of Contents

- [Quick Installation](#quick-installation)
- [Core Concepts](#core-concepts)
- [Tutorials by Skill Level](#tutorials-by-skill-level)
  - [BEGINNER: Get started in 5 minutes](#beginner-get-started-in-5-minutes)
  - [INTERMEDIATE: Real-world applications](#intermediate-real-world-applications)
  - [EXPERT: Production workloads](#expert-production-workloads)
- [API Reference](#api-reference)
- [Troubleshooting & FAQ](#troubleshooting--faq)

---

## Quick Installation

```bash
pip install nucosObs
```

Verify the installation:

```bash
python -m nucosObs
```

You should see output similar to:

```
nucosObs 0.4.17
Python: 3.11.9 (supported >=3.11)
Dependencies: aiohttp 3.9.5, websockets 15.0
Runtime: observers=0, observables=0, loop_closed=False, debug_enabled=False
```

For JSON output (useful for scripts):

```bash
python -m nucosObs --json
```

---

## Core Concepts

### The Observable

An **Observable** is a message bus. Tasks push events into it, and every
registered **Observer** receives every event. Think of it as a publisher that
fan-outs to all subscribers.

```python
from nucosObs.observable import Observable

bus = Observable()
```

### The Observer

An **Observer** listens on an Observable and reacts to events. You subclass
`Observer` and add methods whose names match event directives. Events are
processed one at a time in sequence (per observer).

```python
from nucosObs.observer import Observer

class MyHandler(Observer):
    async def greet(self, name="world"):
        print(f"Hello, {name}!")

bus = Observable()
handler = MyHandler("handler1", bus)
```

### The Event Model

Events are delivered to every registered observer. Two formats are supported:

**Dictionary format** (recommended):

```python
{"name": "method_name", "args": ["arg1", "arg2"]}
```

**String format** (simple commands):

```python
"method_name arg1 arg2"
```

### The Main Loop

You need a running event loop for observers to process events. Use
`main_loop()`:

```python
from nucosObs import main_loop

# ui is an optional list of coroutines to run concurrently
main_loop([])
```

### The Runtime

For simple scripts, the module-level default runtime is sufficient. For
multiple independent applications in one process, create a `Runtime`:

```python
from nucosObs import Runtime
from nucosObs.observable import Observable
from nucosObs.observer import Observer

runtime = Runtime()
bus = Observable(runtime=runtime)
handler = MyHandler("h1", bus, runtime=runtime)

# Works in its own isolated loop
runtime.main_loop([])
runtime.close()
```

---

## Tutorials by Skill Level

---

### BEGINNER: Get started in 5 minutes

#### 1. Hello World — The simplest observer

Create `hello.py`:

```python
import asyncio as aio
from nucosObs import main_loop
from nucosObs.observable import Observable
from nucosObs.observer import Observer

class Greeter(Observer):
    async def say(self):
        print("Hello from nucosObs!")

bus = Observable()
greeter = Greeter("greeter", bus)

# Push an event that calls greeter.say()
aio.ensure_future(bus.put({"name": "say"}))

main_loop([])
```

Run it:

```bash
python hello.py
# Output: Hello from nucosObs!
```

**How it works**:
1. `Greeter` is an `Observer` with method `say()`.
2. `bus` is an `Observable` — the event channel.
3. `bus.put({"name": "say"})` pushes an event. The observer's `parse()` method
   sees `name: "say"` and calls `greeter.say()`.

#### 2. Passing arguments to handlers

```python
class Greeter(Observer):
    async def greet(self, name):
        print(f"Hello, {name}!")

bus = Observable()
greeter = Greeter("greeter", bus)

aio.ensure_future(bus.put({"name": "greet", "args": ["Alice"]}))

main_loop([])
# Output: Hello, Alice!
```

#### 3. Using string commands

```python
aio.ensure_future(bus.put("greet Bob"))
# Same as: {"name": "greet", "args": ["Bob"]}
```

#### 4. Stopping an observer

Send a stop event:

```python
await bus.put({"action": "stop_observer"})
```

The observer finishes its current handler, then stops.

#### 5. Interactive input via stdin

```python
from nucosObs.stdinInterface import StdinInterface

bus = Observable()
greeter = Greeter("greeter", bus)

# Read commands from terminal
ui = StdinInterface(bus).get_ui()

print("Type: 'say', 'greet Alice', or 'x' to exit")
main_loop([ui])
```

Run it and type commands:

```
say             → calls greeter.say()
greet Bob       → calls greeter.greet("Bob")
x               → stops the app
leave_in 3      → waits 3 seconds, then calls greeter.shutdown()
```

---

### INTERMEDIATE: Real-world applications

#### 6. Scheduling recurring tasks

Use `scheduleRegular()` to run a handler periodically:

```python
class SensorReader(Observer):
    async def read_temperature(self):
        print("Reading temperature...")

bus = Observable()
sensor = SensorReader("sensor", bus)

# Call read_temperature() every 2 seconds
sensor.scheduleRegular(sensor.read_temperature, 2.0)

main_loop([])
```

Use `scheduleOnce()` for a delayed single execution:

```python
aio.ensure_future(sensor.scheduleOnce(sensor.read_temperature, 5.0))
# Runs after 5 seconds, exactly once
```

Stop the scheduler without stopping the observer:

```python
sensor.stopSchedule()  # Pauses the schedule loop
sensor.startSchedule() # Resumes it
```

#### 7. Blocking work with `@inThread`

Long-running synchronous operations block the event loop. Use the `@inThread()`
decorator to run them in a thread pool:

```python
from nucosObs.observer import inThread
import time

class DataProcessor(Observer):
    @inThread()
    def compute(self, value):
        """Runs in a thread pool, not blocking the event loop."""
        time.sleep(2)  # Simulate heavy CPU work
        return int(value) * 2

    async def report(self, message):
        print(f"Report: {message}")
```

Observers receive the result of threaded methods via **callbacks**:

```python
class DataProcessor(Observer):
    def __init__(self, name, observable):
        super().__init__(name, observable)
        self.callbacks.update({self.compute: self.on_compute_done})

    @inThread(callback=True)
    def compute(self, value):
        time.sleep(2)
        return int(value) * 2

    async def on_compute_done(self):
        print(f"Compute finished, result cached.")
```

#### 8. Concurrent observers (sharing a queue)

Multiple observers can share a single event queue. This is useful for
load-balancing across workers:

```python
A = Observable()
O1 = DataProcessor("worker1", A)
O2 = DataProcessor("worker2", A, concurrent=["worker1"])

# Events go to either worker1 or worker2, not both
```

Events dispatched to `A` are consumed by whichever observer is idle.

#### 9. Broadcasting events

The `BroadcastObserver` re-dispatches events to all observables:

```python
from nucosObs.observer import BroadcastObserver, broadcast

bus_a = Observable()
bus_b = Observable()
broadcaster = BroadcastObserver("relay", broadcast)

# Send to all observables at once
await broadcast.put({"name": "say", "args": []})
# Both bus_a and bus_b observers receive it
```

#### 10. Routing between observables (TwoWayInterface)

Use `TwoWayInterface` to forward events between named observables:

```python
from nucosObs.twoWayInterface import TwoWayInterface

forward = Observable()
backward = Observable()

interface = TwoWayInterface(
    {"forward": forward, "backward": backward},
    send_all=True  # Events without 'obs' go to ALL observables
)

# Route to a specific observable
await interface.put({"obs": "forward", "name": "say", "args": ["Hello"]})

# Broadcast to all (send_all=True required)
await interface.put({"name": "say", "args": ["Hi everyone"]})

# Stop the interface
await interface.put({"action": "stop interface"})
```

Other supported actions:
- `{"action": "waitTime 2.5"}` — pauses processing for 2.5 seconds
- `{"action": "leave_in 5"}` — waits 5 seconds, then stops

---

### EXPERT: Production workloads

#### 11. WebSocket server with authentication

The framework supports two websocket backends:

- `WebsocketInterface` — uses the `websockets` library (lightweight)
- `AiohttpWebsocketInterface` — uses `aiohttp` (feature-rich, more
  configurable)

Both support TLS, authentication, and client lifecycle management.

**Server example (websockets backend)**:

```python
import ssl
from nucosObs import main_loop
from nucosObs.observable import Observable
from nucosObs.observer import Observer
from nucosObs.websocketInterface import WebsocketInterface

# ---- 1. Define an authenticator ----

class MyAuthenticator:
    async def startAuth(self, message, websocket, nonce):
        """Validate client credentials. Return (connection_id, user) or None."""
        import json
        data = json.loads(message)
        args = data.get("args", {})
        user = args.get("user", "unknown")
        challenge = args.get("challenge", "")
        client_id = args.get("id", "")

        # Verify challenge against nonce and stored secret
        if challenge == expected_challenge(user, nonce):
            await websocket.send(json.dumps({
                "name": "finalizeAuth",
                "args": {"authenticated": True, "id": client_id},
                "action": "authenticated",
            }))
            return client_id, user
        else:
            await websocket.send(json.dumps({
                "name": "finalizeAuth",
                "args": {"authenticated": False, "id": client_id},
                "action": "authenticated",
            }))
            return None, user  # Rejected

# ---- 2. Create an observer that handles authenticated messages ----

class CommandHandler(Observer):
    async def run(self, command, user="unknown"):
        print(f"User '{user}' ran: {command}")

    def parse(self, item):
        # If messages come as JSON strings from WebSocket, parse them
        import json
        try:
            item = json.loads(item)
        except (json.JSONDecodeError, TypeError):
            pass
        return super().parse(item)

# ---- 3. Wire everything together ----

broker = Observable()
handler = CommandHandler("cmd", broker)

wsi = WebsocketInterface(
    broker,
    doAuth=True,
    authenticator=MyAuthenticator(),
    # sslServer=ssl_context,   # Enable TLS in production
)

main_loop([wsi.serve("0.0.0.0", 8765)])
```

**Client example**:

```python
from nucosObs.observable import Observable
from nucosObs.websocketInterface import WebsocketInterface

broker = Observable()

wsi = WebsocketInterface(broker)
main_loop([wsi.connect("127.0.0.1", 8765)])
```

#### 12. Aiohttp WebSocket server with TLS, heartbeat, and reconnection

The `AiohttpWebsocketInterface` provides additional features:

- Configurable heartbeat
- Receive timeouts
- User-aware connection tracking (`send(msg, user)`)
- Automatic cleanup of duplicate user connections (`closeSanely`)

```python
from aiohttp import web
from nucosObs import main_loop
from nucosObs.observable import Observable
from nucosObs.aiohttpWebsocketInterface import AiohttpWebsocketInterface

broker = Observable()

app = web.Application()
wsi = AiohttpWebsocketInterface(
    app,
    broker,
    doAuth=True,
    authenticator=MyAuthenticator(),
    heartbeat=30.0,           # Send ping every 30s
    receive_timeout=60.0,     # Close if no message for 60s
    route="/ws",              # WebSocket endpoint
)

async def start_app():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 5000)
    await site.start()

main_loop([start_app()])
```

**Sending to a specific user**:

```python
class ChatObserver(Observer):
    def __init__(self, name, observable, wsi):
        super().__init__(name, observable)
        self.wsi = wsi

    async def direct_message(self, recipient, text):
        """Send a message directly to one user by name."""
        msg = json.dumps({"from": "server", "text": text})
        await self.wsi.send(msg, recipient)
```

#### 13. Managing multiple isolated runtimes

For multi-tenant or multi-application scenarios, use separate `Runtime`
instances. Each runtime has its own event loop, thread pool, observer
registry, and debug state.

```python
from nucosObs import Runtime
from nucosObs.observable import Observable
from nucosObs.observer import Observer

class Worker(Observer):
    async def process(self, item):
        print(f"[{self.runtime}] Processing {item}")

# Application A
rt_a = Runtime()
bus_a = Observable(runtime=rt_a)
worker_a = Worker("wa", bus_a, runtime=rt_a)

# Application B (completely isolated)
rt_b = Runtime()
bus_b = Observable(runtime=rt_b)
worker_b = Worker("wb", bus_b, runtime=rt_b)

# Each runs independently
rt_a.create_task(bus_a.put({"name": "process", "args": ["A-1"]}))
rt_b.create_task(bus_b.put({"name": "process", "args": ["B-1"]}))

rt_a.main_loop([])  # Blocks until A finishes
rt_a.close()

rt_b.main_loop([])  # Blocks until B finishes
rt_b.close()
```

#### 14. Graceful shutdown with runtime state reporting

`Runtime.shutdown()` sends stop signals to all observers, cancels pending
tasks, and returns a structured report:

```python
report = await runtime.shutdown()
print(report)
# {
#     "already_shutdown": False,
#     "observers": {"total": 3, "open": 3},
#     "tasks": {"pending": 2, "cancelled": 2},
# }
```

Use this to verify clean shutdown in production or tests.

#### 15. Custom error handling with `on_error`

Attach an error callback to catch failures in handlers, parsers, or websocket
operations:

```python
def my_error_handler(context, error):
    print(f"[ERROR] {context}: {error}")

handler = Observer(
    "safe_handler", bus,
    on_error=my_error_handler
)

# For websocket interfaces:
wsi = WebsocketInterface(
    broker,
    on_error=my_error_handler
)
```

Error contexts include: `"parse"`, `"handler"`, `"broadcast"`, `"send"`,
`"authentication"`, `"close_sanely"`, `"on_close"`.

#### 16. WebSocket with TLS and mutual authentication

```python
import ssl

# Server setup
server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
server_ctx.verify_mode = ssl.CERT_REQUIRED
server_ctx.load_cert_chain(certfile="server.crt", keyfile="server.key")
server_ctx.load_verify_locations(cafile="client.crt")

wsi_server = WebsocketInterface(
    broker,
    doAuth=True,
    authenticator=MyAuthenticator(),
    sslServer=server_ctx,
)

# Client setup
client_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
client_ctx.load_cert_chain(certfile="client.crt", keyfile="client.key")
client_ctx.load_verify_locations(cafile="server.crt")

wsi_client = WebsocketInterface(broker, sslClient=client_ctx)
```

#### 17. Bridge methods for session communication

Observers can define bridge methods for communicating with external session
managers:

```python
class SessionAwareObserver(Observer):
    def __init__(self, name, observable):
        super().__init__(name, observable)
        self.set_bridge_method("on_connect", self._handle_connect)

    async def _handle_connect(self, session_id):
        print(f"Session connected: {session_id}")

    async def message(self, text):
        print(f"Message: {text}")
        # Call a bridge method
        await self.bridge("on_connect", "session-123")
```

#### 18. Debug mode

Enable debug output to see event flow:

```python
from nucosObs import debug

debug.append(True)  # Enable verbose logging
# Now every event dispatch, parse attempt, and lifecycle change is printed
```

---

## API Reference

### `nucosObs`

| Function / Class | Description |
|---|---|
| `main_loop(ui)` | Run default runtime with optional list of coroutines |
| `Runtime(loop=None)` | Isolated runtime with own loop, pool, registries |
| `Runtime.create_task(coro)` | Track and run a coroutine in this runtime |
| `Runtime.shutdown()` | Stop all observers, cancel tasks, return report |
| `Runtime.main_loop(ui, test=False)` | Run this runtime's loop |
| `Runtime.close()` | Release thread pool and close the loop |
| `pool` | Default thread pool (4 workers) |
| `debug` | List; append `True` for verbose logging |
| `loop` | Default event loop |
| `get_all_pending_futures(ui)` | Return all observer and schedule coroutines |

### `nucosObs.observable`

| Class / Method | Description |
|---|---|
| `Observable(runtime=None)` | Create an event bus (uses default runtime if omitted) |
| `register(observer, concurrent=[])` | Register an observer; `concurrent` shares queues |
| `put(event)` | Push a dict or string event to all observers |

### `nucosObs.observer`

| Class / Method | Description |
|---|---|
| `Observer(name, observable, concurrent=[], runtime=None, on_error=None)` | Base observer class |
| `parse(item)` | Override to customize event parsing logic |
| `scheduleRegular(method, interval, *args, **kwargs)` | Call `method` every `interval` seconds |
| `scheduleOnce(method, delay, *args, **kwargs)` | Call `method` once after `delay` seconds |
| `stopSchedule()` | Pause the schedule loop |
| `startSchedule()` | Resume the schedule loop |
| `shutdown()` | Request observer stop |
| `set_bridge_method(name, handler)` | Register a bridge method |
| `bridge(method, *args)` | Call a registered bridge method |
| `BroadcastObserver(name, observable)` | Observer that re-dispatches to all observables |
| `@inThread(callback=False)` | Decorator for blocking methods (runs in thread pool) |

### `nucosObs.stdinInterface`

| Class / Method | Description |
|---|---|
| `StdinInterface(observable, input_stream=None, loop=None)` | Read commands from stdin |
| `get_ui()` | Coroutine that processes stdin input |

### `nucosObs.twoWayInterface`

| Class / Method | Description |
|---|---|
| `TwoWayInterface(observables_dict, send_all=False)` | Route events between named observables |
| `put(directive)` | Queue a directive for routing |

### `nucosObs.websocketInterface`

| Class / Method | Description |
|---|---|
| `WebsocketInterface(broker, doAuth=False, ...)` | Lightweight websocket interface |
| `serve(ip, port)` | Start a websocket server |
| `connect(host, port)` | Connect as a websocket client |
| `broadcast(msg, client=None)` | Send to all or one client |
| `shutdown()` | Close all connections and stop observers |

### `nucosObs.aiohttpWebsocketInterface`

| Class / Method | Description |
|---|---|
| `AiohttpWebsocketInterface(app, broker, ...)` | aiohttp-based websocket interface |
| `send(msg, user)` | Send to a specific user |
| `send_by_id(msg, id_)` | Send by connection ID |
| `send_by_client(msg, client)` | Send by client index |
| `broadcast(msg)` | Send to all clients |
| `connect(host, port)` | Connect as a client |
| `shutdown()` | Close all connections and stop observers |

### Supported StdinInterface Commands

| Command | Action |
|---|---|
| `method_name arg1 arg2` | Calls the observer method with arguments |
| `x` | Stops the app (calls observer shutdown) |
| `leave_in N` | Waits N seconds, then shuts down |
| `say` | Calls `observer.say()` (example) |
| `fact N` | Calls `observer.fact(N)` (example) |

### Supported TwoWayInterface Actions

| Directive Action | Behavior |
|---|---|
| `{"obs": "name", "name": "method", "args": []}` | Route to named observable |
| `{"name": "method", "args": []}` | Route to all (if `send_all=True`) |
| `{"action": "waitTime 2.5"}` | Pause processing for 2.5s |
| `{"action": "stop interface"}` | Stop the interface and all observers |
| `{"action": "leave_in 5"}` | Wait 5s, then stop |

---

## Troubleshooting & FAQ

**Q: Events are being sent but nothing happens.**

Check that:
1. The observer method name matches the `"name"` field exactly (case-sensitive).
2. The observer and observable share the same `Runtime`.
3. The event loop is running (`main_loop()` must be called).
4. Debug mode might help: add `from nucosObs import debug; debug.append(True)`.

**Q: My handler blocks the whole application.**

Wrap it with `@inThread()`:

```python
@inThread()
def my_blocking_function(self, arg):
    # This runs in a thread pool
    time.sleep(5)
```

**Q: How do I stop the app from code?**

```python
await bus.put({"action": "stop_observer"})
```

For a clean shutdown with state reporting:

```python
report = await runtime.shutdown()
```

**Q: WebSocket client connects but authentication fails.**

1. Verify your `Authenticator.startAuth()` returns `(connection_id, user)` on
   success and `(None, user)` on failure.
2. Check that `doAuth=True` is set on the interface.
3. The nonce is sent automatically; your client must respond with a challenge
   that matches the server's expected computation.
4. Enable debug mode to see the authentication flow: `debug.append(True)`.

**Q: Message delivery failed — where do I see the error?**

Attach an `on_error` callback:

```python
def log_error(context, error):
    print(f"[{context}] {error}")

observer = Observer("safe", bus, on_error=log_error)
```

**Q: Multiple runtimes aren't isolated.**

Ensure every object explicitly receives its runtime:

```python
rt = Runtime()
bus = Observable(runtime=rt)      # explicit
obs = Observer("o", bus, runtime=rt)  # explicit
```

If you omit `runtime`, the default module-level runtime is used, sharing state.

**Q: The `nucosCR` package is not installed.**

`nucosObs` works without it. Token generation falls back to Python's
`secrets.token_urlsafe()`. `nucosCR` is only needed for custom
challenge-response authentication.

---

## Development & Testing

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
python -m pytest
```

Run with coverage:

```bash
python -m pytest --cov=nucosObs --cov-report=term-missing
```

---

## Related Resources

- [CHANGELOG.md](CHANGELOG.md) — Release history
- [FINAL_READINESS.md](FINAL_READINESS.md) — Coverage and proposal status
- [CONTRIBUTING.md](../CONTRIBUTING.md) — How to contribute
- [examples/](../examples/) — Full runnable examples