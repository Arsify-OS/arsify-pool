# Large File Analysis Strategy

**Problem:** Analyzing large codebases (>100KB, 1000+ lines) causes context exhaustion, multiple compressions, and API credit drain.

**Session:** 2026-05-03 - Regrow Up World game analysis (332KB HTML, 6512 lines)

## Symptoms

- Agent reads same file 6+ times trying to fit it in context
- Multiple context compressions (7-9 compressions observed)
- API errors: "context length exceeded", "prompt tokens limit exceeded"
- Credit exhaustion on expensive models (claude-opus-4.6)

## Root Cause

Standard approach of reading full file → analyze → write report doesn't work when:
- File size > 100KB
- Combined with tool schemas (8,901 tokens)
- Model has limited context (128k tokens)
- Multiple read attempts compound the problem

## Solution: Strategic Code Sampling

Instead of reading the entire file, sample key sections:

### 1. Get File Metadata First
```python
# Get line count and structure
terminal(command="wc -l file.html")
terminal(command="grep -n '<script>' file.html | head -5")
```

### 2. Read Strategic Sections
```python
# Read first 100 lines (headers, imports, config)
read_file(path="file.html", limit=100)

# Read specific sections by offset
read_file(path="file.html", offset=1400, limit=150)  # HTML structure
read_file(path="file.html", offset=3622, limit=200)  # Main game engine
read_file(path="file.html", offset=2497, limit=200)  # Economy system
```

### 3. Use grep/awk for Pattern Extraction
```bash
# Find all class definitions
grep -n "^class " file.py

# Extract function signatures
awk '/^function / {print NR": "$0}' file.js

# Find all const/let declarations
grep -E "^(const|let) " file.js | head -20
```

### 4. Analyze in Chunks
Break analysis into multiple focused tasks:
- Task 1: Architecture overview (read 300 lines total)
- Task 2: Data models (read specific sections)
- Task 3: Integration points (targeted grep searches)

## Example: 332KB HTML Game File

**Failed approach:**
```python
# This caused 9 context compressions and credit exhaustion
read_file(path="game.html")  # 6512 lines
# Agent tries to analyze entire file at once
```

**Successful approach:**
```python
# 1. Get structure
terminal(command="wc -l game.html")
terminal(command="grep -n '<script>' game.html")

# 2. Sample key sections (total ~600 lines read)
read_file(path="game.html", limit=100)           # Header
read_file(path="game.html", offset=3622, limit=200)  # Game engine
read_file(path="game.html", offset=2497, limit=200)  # Economy system

# 3. Extract patterns
search_files(path="game.html", pattern="class|function|const")

# 4. Analyze samples, not full file
# Write architecture.md based on strategic samples
```

**Result:** Complete analysis in 7 minutes with no context issues.

## Model Selection for Large Files

| Model | Context | Cost | Recommendation |
|-------|---------|------|----------------|
| claude-opus-4.6 | 200k | High | ❌ Avoid for large files |
| gpt-4o-mini | 128k | Low | ✅ Good for sampling |
| gpt-4o | 128k | Medium | ✅ Good balance |
| claude-sonnet-4 | 200k | Medium | ✅ Good for complex analysis |

**Tip:** Use cheaper models (gpt-4o-mini) for worker agents doing large file analysis. Reserve expensive models for orchestration and final synthesis.

## When to Use Full Read vs Sampling

**Full read (safe):**
- File < 50KB
- < 1000 lines
- Simple structure (config files, small scripts)

**Strategic sampling (required):**
- File > 100KB
- > 2000 lines
- Complex structure (bundled apps, minified code)
- Multiple files to analyze in one session

## Automation Pattern

```python
def analyze_large_file(path):
    # 1. Check size
    result = terminal(command=f"wc -l {path}")
    lines = int(result.split()[0])
    
    if lines < 1000:
        # Small file - read fully
        return read_file(path=path)
    
    # 2. Large file - sample strategically
    samples = []
    samples.append(read_file(path=path, limit=100))  # Header
    
    # Find key sections (e.g., script blocks)
    sections = terminal(command=f"grep -n '<script>' {path}")
    for section_line in parse_sections(sections):
        samples.append(read_file(path=path, offset=section_line, limit=200))
    
    # 3. Extract patterns
    patterns = search_files(path=path, pattern="class|function|const")
    
    return {"samples": samples, "patterns": patterns}
```

## Credit Management

**Problem:** OpenRouter free tier has token limits (e.g., 78k tokens remaining).

**Solutions:**
1. Use cheaper models for analysis tasks
2. Set explicit `max_tokens` in requests to prevent over-allocation
3. Monitor credit usage: check OpenRouter dashboard before large tasks
4. Switch to local models (Ollama) for development/testing
5. Use multiple API keys with credential pooling

**Config example:**
```yaml
model:
  default: "openai/gpt-4o-mini"  # Cheap model for workers
  provider: "openrouter"

# For orchestrator/main agent, use better model
# hermes chat -m "anthropic/claude-sonnet-4" -q "..."
```

## Summary

- **Don't read large files fully** - sample strategically
- **Use grep/awk** for pattern extraction
- **Break analysis into chunks** - multiple focused tasks
- **Choose cheaper models** for large file analysis
- **Monitor API credits** before starting large tasks
