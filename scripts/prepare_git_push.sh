#!/usr/bin/env bash
# =============================================================
# prepare_git_push.sh
# Removes tracked files that should now be ignored by .gitignore
# Run this ONCE before pushing to GitHub to clean up the index.
# =============================================================
set -euo pipefail

echo "======================================================"
echo "  Preparing repository for a clean GitHub push"
echo "======================================================"

# --- Step 1: Remove files from Git index that are now in .gitignore ---
echo ""
echo "Step 1: Removing ignored files from Git tracking..."

# macOS artifacts
git rm --cached -r --ignore-unmatch .DS_Store '**/.DS_Store' 2>/dev/null || true

# Python cache
git rm --cached -r --ignore-unmatch '**/__pycache__' 2>/dev/null || true

# Word temp lock files
git rm --cached --ignore-unmatch '~$*' 2>/dev/null || true
git rm --cached --ignore-unmatch '~\$*' 2>/dev/null || true

# Backup files
git rm --cached --ignore-unmatch '*.bak' docker-compose.yml.bak 2>/dev/null || true

# Stray submission files at root
git rm --cached --ignore-unmatch 'Kasarala-Vamshi_*.txt' 2>/dev/null || true
git rm --cached --ignore-unmatch 'Kasarla-Vamshi_*.txt' 2>/dev/null || true
git rm --cached --ignore-unmatch 'Phase2_PebblePad_Text.*' 2>/dev/null || true
git rm --cached --ignore-unmatch 'PROJECT_STRUCTURE.md' 2>/dev/null || true

# Old submission folders
git rm --cached -r --ignore-unmatch Phase2_Submission/ 2>/dev/null || true
git rm --cached -r --ignore-unmatch submissions/ 2>/dev/null || true
git rm --cached -r --ignore-unmatch submissionready/ 2>/dev/null || true

# Empty placeholder directories
git rm --cached -r --ignore-unmatch config/ 2>/dev/null || true
git rm --cached -r --ignore-unmatch src/ 2>/dev/null || true
git rm --cached -r --ignore-unmatch data/ 2>/dev/null || true

echo "Done removing cached files."

# --- Step 2: Show what will be committed ---
echo ""
echo "Step 2: Current Git status:"
echo "------------------------------------------------------"
git status --short

# --- Step 3: Show clean file list ---
echo ""
echo "Step 3: Files that WILL be on GitHub after push:"
echo "------------------------------------------------------"
git ls-files --cached | sort

echo ""
echo "======================================================"
echo "  Ready! Now run:"
echo "    git add -A"
echo "    git commit -m 'Clean up repo structure for Phase 2 submission'"
echo "    git push origin main"
echo "======================================================"
