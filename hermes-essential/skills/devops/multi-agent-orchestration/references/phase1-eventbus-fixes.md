# Phase 1 EventBus Implementation Fixes

## Problem: Pattern Subscription Not Working

When subscribing to Redis pattern `hermes:*`, events were published but not received by subscribers.

### Root Cause

1. **Channel Decoding**: Redis returns channel names as bytes, but subscriber dictionary keys are strings
2. **Pattern Matching Logic**: Redis `psubscribe()` subscribes to pattern, but the message handler needs explicit pattern matching logic

### Solution

#### 1. Decode Channel Names

```python
def _handle_message(self, message: Dict):
    """Handle incoming message."""
    try:
        # Get channel (decode if bytes)
        channel = message.get("channel") or message.get("pattern")
        if not channel:
            return
        
        # Decode channel if bytes
        if isinstance(channel, bytes):
            channel = channel.decode('utf-8')
```

#### 2. Add Pattern Matching Logic

```python
        # Call subscribers for exact channel match
        if channel in self.subscribers:
            for callback in self.subscribers[channel]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event callback: {e}")
        
        # Call subscribers for pattern matches
        for pattern, callbacks in self.subscribers.items():
            if '*' in pattern or '?' in pattern:
                # Simple pattern matching
                import fnmatch
                if fnmatch.fnmatch(channel, pattern):
                    for callback in callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            print(f"Error in pattern callback: {e}")
```

### Testing

```python
from orchestrator import EventBus, EventType
import time

bus = EventBus()
bus.start()

events_received = []
def test_callback(event):
    events_received.append(event.event_type)
    print(f'Received: {event.event_type}')

# Subscribe to pattern
bus.subscribe_pattern('hermes:*', test_callback)

# Publish events
bus.publish_event(EventType.TASK_SUBMITTED, {'task_id': 'test-001'})
bus.publish_event(EventType.AGENT_REGISTERED, {'agent_id': 'test-agent'})

time.sleep(1)

assert len(events_received) >= 2, "Pattern subscription not working"
bus.stop()
```

### Key Takeaways

- Redis Pub/Sub pattern subscription (`psubscribe`) only subscribes to the pattern—it doesn't automatically match patterns in your code
- You must implement pattern matching logic in the message handler
- Always decode bytes from Redis to strings for comparison
- Use `fnmatch` for glob-style pattern matching (`*`, `?`)
- Test both exact channel subscription and pattern subscription separately

## Implementation Location

File: `/usr/local/lib/hermes-orchestrator/orchestrator/event_bus.py`
Method: `EventBus._handle_message()`
