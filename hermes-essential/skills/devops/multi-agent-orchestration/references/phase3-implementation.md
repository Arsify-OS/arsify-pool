# Phase 3 Implementation: Advanced Features

## Overview
Phase 3 adds three advanced features to the multi-agent orchestration system:
1. DAG Workflows (task dependencies)
2. Agent Auto-scaling (monitoring queue depth)
3. Distributed Tracing (OpenTelemetry)

## 1. DAG Workflows

### Task Model Extensions
Location: `/usr/local/lib/hermes-orchestrator/orchestrator/task_queue.py`

Add to Task class:
```python
self.dependencies = dependencies or []
self.workflow_id = workflow_id
```

### Redis Data Structures
- `hermes:dag:blocked_tasks` - Set of blocked task IDs
- `hermes:dag:dependents:{task_id}` - Set of task IDs that depend on this task

### Key Methods Added to TaskQueue
- `_get_dependents(task_id)` - Get tasks that depend on a task
- `_activate_task(task_id)` - Move blocked task to ready queue
- `_process_dependents(completed_task_id)` - Check and activate satisfied dependencies

### Flow
1. Task with dependencies → added to `hermes:dag:blocked_tasks` set
2. For each dependency, add task to `hermes:dag:dependents:{dep_id}`
3. When task completes → call `_process_dependents()`
4. For each dependent, check if ALL its dependencies are completed
5. If all met → `_activate_task()` moves it to ready queue

### submit_task Modification
```python
if dependencies:
    self.redis.sadd("hermes:dag:blocked_tasks", task_id)
    for dep_id in dependencies:
        self.redis.sadd(f"hermes:dag:dependents:{dep_id}", task_id)
else:
    # Add to normal queue
```

## 2. Agent Auto-scaling

### Monitoring Script
Location: `/usr/local/lib/hermes-orchestrator/auto_scaling.py`

Simple queue-depth monitor:
- Threshold-based: scale out if queue > 10, scale in if queue < 2
- Checks active agents via AgentRegistry
- Prints recommendations (no actual scaling implemented)

### Scaling Considerations
- Systemd services: `/etc/systemd/system/hermes-*.service`
- Templates needed for dynamic agent creation
- Actual scaling requires integration with orchestration layer

## 3. Distributed Tracing

### OpenTelemetry Integration
Location: `/usr/local/lib/hermes-orchestrator/api.py`

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# After app creation:
FastAPIInstrumentor().instrument_app(app)
```

### Packages
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi
```

### Next Steps for Production
- Replace ConsoleSpanExporter with Jaeger or Grafana Tempo exporter
- Add tracing to agent SDK
- Propagate trace context across agent boundaries

## Test Script
Location: `/usr/local/lib/hermes-orchestrator/test_dag.py`

Verifies:
- Task A submitted without dependencies
- Task B submitted with dependency on A → blocked
- Completing A → B automatically unblocked and moved to queue
