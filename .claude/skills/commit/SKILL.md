---
name: commit
description: Commit work to git with proper formatting
disable-model-invocation: true
allowed-tools: Bash(git *)
argument-hint: "[message]"
---

# Commit to Git

```bash
git status                          # Check what will be committed
git add <files>                     # Stage changes
git commit -m "Your message"        # Commit
```

## Message Format

- Start with action verb (Fix, Add, Update, Refactor)
- Reference packet if applicable: `Complete EXE-001: Description`
- 50-72 characters for first line
- Add details in body for complex changes

## Examples

```
Complete EXE-001: Document pipeline architecture
```

```
Fix race condition in order processing
```
