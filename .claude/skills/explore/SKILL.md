---
name: explore
description: Explore and understand unfamiliar codebases
allowed-tools: Read, Grep, Glob, Bash(find *), Bash(wc *)
argument-hint: "[question or area to explore]"
---

# Explore Codebase

## Strategy

1. **Structure**: `find . -type d -not -path '*/\.*' | head -20`
2. **Entry points**: Look for `main.py`, `index.js`, `app.py`
3. **Patterns**: grep for routes, queries, exports
4. **Trace features**: Find definition → find usages → follow data flow

## Common Searches

```bash
grep -rn "keyword" --include="*.py"          # Find occurrences
grep -rn "function_name(" --include="*.py"   # Find usages
find . -name "*model*" -o -name "*schema*"   # Find data models
```

## Report Format

```markdown
## Summary
[Answer]

## Key Files
- `path/file.py` — purpose

## How It Works
1. Step
2. Step
```
