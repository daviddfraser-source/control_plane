---
name: create-pr
description: Create a pull request with proper formatting
allowed-tools: Bash(git *), Bash(gh *)
argument-hint: "[title]"
---

# Create Pull Request

## Steps

```bash
git push -u origin $(git branch --show-current)

gh pr create --title "Your title" --body "$(cat <<'EOF'
## Summary
Brief description.

## Changes
- Change 1
- Change 2

## Testing
- [ ] Tests pass
- [ ] Manual testing done

## WBS Reference
Packet: EXE-XXX
EOF
)"
```

## Title Rules

- Imperative mood: "Add feature" not "Added feature"
- Under 72 characters
- Descriptive: what, not how
