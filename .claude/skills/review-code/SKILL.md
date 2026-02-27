---
name: review-code
description: Review code changes for quality, bugs, and best practices
allowed-tools: Bash(git *), Read, Grep, Glob
argument-hint: "[file or commit range]"
---

# Code Review

```bash
git diff --cached           # Staged changes
git diff HEAD~3..HEAD       # Recent commits
```

## Checklist

- **Correctness**: Logic, edge cases, error handling
- **Security**: No secrets, input validation, no injection
- **Quality**: Readable, focused functions, no duplication
- **Testing**: Has tests, covers edge cases
- **Performance**: No N+1, no unnecessary loops

## Report Format

```markdown
## Summary
[approved / needs changes / blocked]

## Critical (must fix)
- file:line - issue

## Important (should fix)
- file:line - issue

## Suggestions
- file:line - idea
```
