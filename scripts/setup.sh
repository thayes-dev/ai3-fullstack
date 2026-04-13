#!/bin/bash
# AI-3: First-Time Setup
# Run this ONCE after cloning the repository.

set -e

echo "========================================="
echo "  AI-3: Full Stack AI Engineering Setup"
echo "========================================="
echo ""

# 1. Configure git merge strategy for student-owned files
git config merge.ours.driver true
echo "[OK] Git merge strategy configured (your customizations are safe on pull)"

# 2. Create .env from template if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[OK] Created .env from template"
    echo "     >> NEXT: Edit .env and add your API keys"
else
    echo "[OK] .env already exists"
fi

# 3. Check Python version
python_version=$(python3 --version 2>&1)
echo "[OK] Python: $python_version"

echo ""
echo "========================================="
echo "  Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env and fill in your API keys:"
echo "     - ANTHROPIC_API_KEY (from console.anthropic.com)"
echo "     - VOYAGE_API_KEY (from dash.voyageai.com)"
echo "     - PHOENIX_API_KEY (from app.phoenix.arize.com → Settings → API Keys)"
echo "     - PHOENIX_PROJECT_NAME (e.g., ai3-yourname)"
echo ""
echo "  2. Install dependencies:"
echo "     uv sync"
echo ""
echo "  3. Verify everything works:"
echo "     python -c \"from pipeline.generation.generate import call_claude; print('OK')\""
echo ""
