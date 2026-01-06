# Dockerfile Path Selection

## Your Options

Railway is showing you two options:
1. `questdb/Dockerfile` ✅ **Choose this one**
2. `Dockerfile` (probably looking in root)

## Recommendation: Choose `questdb/Dockerfile`

**Why:**
- Your Dockerfile is located at `questdb/Dockerfile` in your repository
- This is the full path from repository root
- Railway will find it correctly

## If You Set Root Directory

If you also set **Root Directory** to `questdb/`:
- Build context becomes `questdb/`
- You might need to change Dockerfile path to just `Dockerfile`
- But start with `questdb/Dockerfile` first - it's safer

## Quick Answer

**Select: `questdb/Dockerfile`** ✅

This is the correct path to your Dockerfile in the repository.



