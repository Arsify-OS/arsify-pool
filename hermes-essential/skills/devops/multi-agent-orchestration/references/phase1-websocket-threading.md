# Phase 1 WebSocket Threading Solution

## Problem: WebSocket Broadcasting from Background Thread

EventBus runs in a background thread, but FastAPI/WebSocket runs in the main asyncio event loop. Attempting to broadcast events from the EventBus thread fails with:

```
Broadcast error: There is no current event loop in thread 'Thread-1 (_listen)'.
```

### Root Cause

- FastAPI runs in the main asyncio event loop
- EventBus listener runs in a separate background thread (started via `threading.Thread`)
- Background threads don't have an event loop
- Cannot use `asyncio.create_task()` or `asyncio.ensure_future()` from a thread without an event loop

### Failed Approaches

#### Attempt 1: `asyncio.create_task()`
```python
def broadcast_event(event):
    asyncio.create_task(manager.broadcast(...))  # ❌ No event loop in thread
```

#### Attempt 2: `asyncio.get_event_loop()` + `ensure_future()`
```python
def broadcast_event(event):
    loop = asyncio.get_event_loop()  # ❌ Returns None or wrong loop
    asyncio.ensure_future(manager.broadcast(...))
```

### Solution: Store Main Loop Reference

#### Step 1: Declare Global Loop Variable

```python
# At module level in api.py
manager = ConnectionManager()

# Store main event loop reference
main_loop = None
```

#### Step 2: Capture Loop at Startup

```python
@app.on_event("startup")
async def startup_event():
    global main_loop
    
    # Store the main event loop
    main_loop = asyncio.get_event_loop()
    
    orchestrator.event_bus.start()
    orchestrator.knowledge_sync.start()
    
    # Subscribe to all events for WebSocket broadcasting
    orchestrator.event_bus.subscribe_pattern("hermes:*", broadcast_event)
```

#### Step 3: Use `run_coroutine_threadsafe()`

```python
async def broadcast_event_async(event):
    """Broadcast event to all WebSocket clients (async)."""
    await manager.broadcast(json.dumps({
        "event_type": event.event_type,
        "data": event.data,
        "source": event.source,
        "timestamp": event.timestamp
    }))

def broadcast_event(event):
    """Broadcast event to all WebSocket clients (from thread)."""
    global main_loop
    try:
        if main_loop and main_loop.is_running():
            # Schedule the coroutine in the main loop
            asyncio.run_coroutine_threadsafe(broadcast_event_async(event), main_loop)
    except Exception as e:
        print(f"Broadcast error: {e}")
```

### How It Works

1. **Startup**: FastAPI startup event captures the main asyncio event loop
2. **Background Thread**: EventBus listener thread receives Redis events
3. **Cross-thread Call**: `asyncio.run_coroutine_threadsafe()` schedules the coroutine in the main loop
4. **Execution**: Main loop executes the broadcast coroutine, sending to all WebSocket clients

### Key API: `asyncio.run_coroutine_threadsafe()`

```python
asyncio.run_coroutine_threadsafe(coro, loop)
```

- **Purpose**: Submit a coroutine to an event loop from another thread
- **Returns**: `concurrent.futures.Future` (can be ignored if fire-and-forget)
- **Thread-safe**: Yes, designed for cross-thread communication
- **Use case**: Background threads need to schedule work in the main asyncio loop

### Testing

```python
# Test script: test_event_broadcast.py
import asyncio
import websockets
import requests
import time

async def listen_events():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        # Receive welcome
        msg = await ws.recv()
        print(f"Connected: {msg}")
        
        # Listen for events
        events = []
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                data = json.loads(msg)
                events.append(data['event_type'])
                print(f"Event: {data['event_type']}")
        except asyncio.TimeoutError:
            pass
        
        return events

async def main():
    # Start listener
    listener = asyncio.create_task(listen_events())
    await asyncio.sleep(0.5)
    
    # Trigger events via API
    requests.post("http://localhost:8000/agents/register", json={
        "agent_id": "test-agent",
        "agent_name": "Test Agent",
        "capabilities": ["testing"]
    })
    
    requests.post("http://localhost:8000/tasks", json={
        "task_type": "test",
        "description": "Test task"
    })
    
    # Wait for events
    events = await listener
    assert len(events) >= 2, f"Expected 2+ events, got {len(events)}"
    print(f"✅ Received {len(events)} events: {events}")

asyncio.run(main())
```

### Alternative: Queue-based Approach

If you need more control or want to avoid global state:

```python
import asyncio
import queue

# Thread-safe queue
event_queue = queue.Queue()

def broadcast_event(event):
    """Called from background thread."""
    event_queue.put(event)

async def event_broadcaster():
    """Runs in main loop."""
    while True:
        try:
            event = event_queue.get_nowait()
            await manager.broadcast(json.dumps(event.to_dict()))
        except queue.Empty:
            await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup():
    asyncio.create_task(event_broadcaster())
```

### Key Takeaways

- **Never** call async functions directly from sync threads
- **Never** use `asyncio.create_task()` from threads without event loops
- **Always** use `asyncio.run_coroutine_threadsafe()` for cross-thread async calls
- **Store** the main event loop reference at startup if needed across modules
- **Check** `loop.is_running()` before scheduling to avoid errors during shutdown

## Implementation Location

File: `/usr/local/lib/hermes-orchestrator/api.py`
Functions: `broadcast_event()`, `broadcast_event_async()`, `startup_event()`
