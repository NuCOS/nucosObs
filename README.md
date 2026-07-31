# nucosObs
*nucosObs* serves as an observer-observable framework based on ``asyncio``.

![Current Version PyPI](https://img.shields.io/pypi/v/nucosObs.svg)

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


## Licence
MIT License

## Platforms
No specific platform dependency. Python 3.5 is minimum.


