# Terminal Tool Fixes
## FileNotFoundError when cwd is deleted
Hermes Agent's `tools/terminal_tool.py` raises `FileNotFoundError` if the current working directory is deleted when calling `os.getcwd()`. This breaks all terminal tool calls until the agent is restarted or the directory is recreated.

### Root Cause
Two unhandled `os.getcwd()` calls in `_get_env_config()`:
1. Line 1018: Sets `default_cwd` for local terminal environments
2. Line 1040: Sets `docker_cwd_source` for Docker cwd passthrough

### Patched Code
#### 1. default_cwd assignment (line 1018)
```python
if env_type == "local":
    try:
        default_cwd = os.getcwd()
    except FileNotFoundError:
        # Fallback to /root if cwd is deleted
        default_cwd = "/root"
```

#### 2. docker_cwd_source assignment (line 1040)
```python
_env_cwd = os.getenv("TERMINAL_CWD")
if _env_cwd:
    docker_cwd_source = _env_cwd
else:
    try:
        docker_cwd_source = os.getcwd()
    except FileNotFoundError:
        docker_cwd_source = "/root"
```

### Verification
After patching, recreate the deleted directory and test:
```bash
mkdir -p /root/hermes-workspace
python3 -c "import os; os.getcwd()"  # Should not raise error
```
