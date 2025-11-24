# Git Workflow Best Practices

This document outlines the recommended Git workflow for this project, covering both human developers and AI assistant sessions.

## Core Principle: Short-Lived Feature Branches

Feature branches should be:
- **Created fresh** from main for each distinct piece of work
- **Merged** via pull request
- **Deleted immediately** after merge (never reused)

## GitHub Repository Settings

### Enable Auto-Delete Branches

Configure your repository to automatically delete branches after PR merge:

1. Go to repository **Settings** → **General**
2. Scroll to **Pull Requests**
3. Check **Automatically delete head branches**

This ensures merged branches are removed from GitHub immediately, preventing accidental reuse.

## Local Workflow for Humans

### Starting New Work

```bash
git checkout main
git pull origin main
git checkout -b feature/descriptive-name
# Make changes, commit
```

### After Your PR Is Merged

When GitHub auto-deletes the remote branch:

1. **Update your local git knowledge:**
   ```bash
   git fetch --prune
   ```
   This updates your local tracking of what's on GitHub.

2. **Delete your local branch:**
   ```bash
   git checkout main
   git pull origin main
   git branch -d feature/branch-name
   ```

   Or use GitHub Desktop's checkbox to delete both local and remote branches when merging.

### Periodic Cleanup

Check for branches you can safely delete:

```bash
# See all merged branches (safe to delete)
git branch --merged main

# See which local branches have deleted remotes
git branch -vv | grep ': gone]'
```

Delete merged branches:
```bash
git branch -d branch-name
```

## Workflow for AI Assistant Sessions

When working with AI assistants like Claude Code, the assistant maintains context across a long conversation. This creates a unique challenge: if you merge a PR mid-session and continue working, the AI will keep committing to the same branch.

### After Creating a PR

The AI should ask:
```
"Let me know when the PR is merged so I can start a fresh branch for any additional work."
```

### After Merging a PR

Explicitly tell the AI to start fresh:
```
"The PR was merged. Start a fresh branch from main for the next task."
```

The AI will then:
```bash
git checkout main
git pull origin main
git checkout -b feature/next-thing
```

**Why this matters:** Without this explicit reset, the AI continues on the merged branch, causing divergent histories and merge conflicts on the next PR.

See [AI_Workflow.md](AI_Workflow.md) for more details on working with AI assistants.

## Checking Branch Status Before Work

Before making changes, verify your branch is safe to use:

### Is this branch already merged?
```bash
git branch --merged main | grep $(git branch --show-current)
```
If your current branch appears, **it's already merged** — switch to a fresh branch.

### Was the remote branch deleted?
```bash
git branch -vv
```
If you see `[origin/branch-name: gone]`, the remote was deleted — this branch shouldn't be reused.

## Common Scenarios

### "I merged on GitHub, but my local branch looks untouched"

This is normal! Merging on GitHub doesn't affect your local branch. The branch still exists locally with all its commits.

**What to do:**
1. Run `git fetch --prune` to learn about the remote deletion
2. Switch to main: `git checkout main`
3. Pull the merge: `git pull origin main`
4. Delete the old branch: `git branch -d old-branch`
5. Your changes are now in main — the old branch is obsolete

### "I kept working on a branch after its PR merged"

**Symptoms:** When you try to create a new PR, you get merge conflicts on files you didn't change.

**Why it happens:** Your branch contains:
- Old commits (already in main via the merged PR)
- New commits (not in main yet)

Git sees this as divergent history.

**Solution:**
1. Create a fresh branch from main
2. Copy your new changes to the fresh branch
3. Create PR from the fresh branch

**Prevention:** Always start a fresh branch after a PR merges.

## Summary: The Happy Path

1. **Configure GitHub** to auto-delete merged branches
2. **Create feature branch** from main for each task
3. **Create PR** when work is complete
4. **Merge PR** on GitHub (auto-deletes remote)
5. **Update local:**
   ```bash
   git fetch --prune
   git checkout main
   git pull origin main
   git branch -d feature-branch
   ```
6. **For next task:** Create fresh branch from main (go to step 2)

This workflow prevents merge conflicts, keeps your branch list clean, and works seamlessly with both human developers and AI assistants.
