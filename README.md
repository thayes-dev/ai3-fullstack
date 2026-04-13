# AI-3: Full Stack AI Engineering

Welcome to AI-3. Over the next 4 weeks, you will turn the RAG pipeline you built in AI-2 into a deployed, user-facing application — a Streamlit chat app with evaluation, safety defenses, feedback capture, and cloud deployment.

## What You'll Build

A Northbrook Partners Q&A application that:
- Answers questions from the Northbrook knowledge base using improved retrieval (HyDE + enrichment)
- Runs as a Streamlit web application with streaming responses and source citations
- Manages context intelligently (chunk assembly, history truncation)
- Defends against prompt injection attacks
- Captures user feedback and turns it into regression tests
- Deploys to the cloud with a public URL

---

## Prerequisites

### Accounts You Need

Set these up **before Session 1.1**:

| Service | What It's For | How to Get Access |
|---------|--------------|-------------------|
| **Anthropic** | Claude API (answer generation) | [console.anthropic.com](https://console.anthropic.com) — sign up, create an API key |
| **Voyage AI** | Text embeddings (semantic search) | [dash.voyageai.com](https://dash.voyageai.com) — sign up, create an API key |
| **Phoenix (Arize)** | Observability and evaluation | Your instructor has added you — check your email for an invite to [app.phoenix.arize.com](https://app.phoenix.arize.com) |
| **GitHub** | Code repository | You should already have this from AI-2 |

### Software You Need

- **Python 3.12+**
- **uv** (Python package manager) — [installation guide](https://docs.astral.sh/uv/getting-started/installation/)
- **Git**
- A code editor (VS Code recommended)

---

## Setup (Session 1.1)

### 1. Clone the Repository

```bash
git clone https://github.com/<org>/ai3-fullstack.git
cd ai3-fullstack
```

### 2. Run the Setup Script

```bash
bash scripts/setup.sh
```

This does two things:
- Configures Git so your customizations are safe when pulling updates (more on this below)
- Creates a `.env` file from the template

### 3. Install Dependencies

```bash
uv sync
```

### 4. Configure Your API Keys

Open `.env` in your editor and fill in your keys:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-your-actual-key
VOYAGE_API_KEY=pa-your-actual-key
PHOENIX_API_KEY=your-actual-key
PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com
PHOENIX_PROJECT_NAME=ai3-yourname
```

**Getting each key:**

**Anthropic:**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Click "API Keys" in the sidebar
3. Click "Create Key" — name it "AI-3 Course"
4. Copy the key (starts with `sk-ant-`)

**Voyage AI:**
1. Go to [dash.voyageai.com](https://dash.voyageai.com)
2. Click "API Keys"
3. Create a new key
4. Copy the key (starts with `pa-`)

**Phoenix:**
1. Go to [app.phoenix.arize.com](https://app.phoenix.arize.com) and log in
2. You should see the workspace your instructor set up
3. Go to **Settings** (gear icon) → **API Keys**
4. Click "Create System Key"
5. Copy the key
6. For `PHOENIX_PROJECT_NAME`, use `ai3-` followed by your name (e.g., `ai3-tyler`). This keeps your traces separate from other students.

### 5. Verify Everything Works

```bash
# Check imports
python -c "from pipeline.generation.generate import call_claude; print('Generation: OK')"
python -c "from pipeline.retrieval.naive import naive_retrieve; print('Retrieval: OK')"

# Check ChromaDB is loaded
python -c "from pipeline.ingestion.store import get_collection; print(f'ChromaDB: {get_collection().count()} chunks loaded')"

# Test a real API call (costs a few cents)
python -c "
from pipeline.generation.generate import call_claude
print(call_claude('Say hello in exactly 3 words.'))
"
```

**If something fails:**
- `ModuleNotFoundError` → Did you run `uv sync`?
- `AuthenticationError` → Is your `.env` populated with real keys?
- `ChromaDB: 0 chunks` → The database may not have loaded. Ask your instructor.

---

## Repository Structure

```
ai3-fullstack/
├── pipeline/            ← Reference pipeline from AI-2 (do not modify directly)
│   ├── generation/      ← Claude API wrapper (call_claude, call_claude_with_usage)
│   ├── embeddings/      ← Voyage AI embeddings (get_embedding, embed_texts)
│   ├── ingestion/       ← Document chunking + ChromaDB storage
│   ├── retrieval/       ← RAG retrieval (naive, filtered — you'll add HyDE + enrichment)
│   └── observability/   ← Phoenix logging and tracing
│
├── data/northbrook/     ← The Northbrook Partners document corpus
├── chroma_db/           ← Pre-populated vector database (do not delete)
│
├── notebooks/           ← Exploration notebooks for in-class work
│   └── my_work/         ← YOUR scratch space (not tracked by git)
│
├── feedback/            ← Feedback JSON storage (added later in the course)
├── my_work/             ← Another scratch space for personal experiments
│
├── app/                 ← Streamlit application (added in Session 2.1)
├── tests/               ← Test suites (added over the course)
├── scripts/setup.sh     ← One-time setup script
│
├── .env                 ← YOUR API keys (never committed to git)
├── .env.example         ← Template showing what keys you need
├── .gitattributes       ← Merge rules that protect your customizations
├── .gitignore           ← Files excluded from git tracking
└── pyproject.toml       ← Python dependencies
```

---

## How Updates Work

Your instructor will push new code after each session (new modules, app updates, etc.). To get these updates:

```bash
# 1. Save your current work first
git add -A
git commit -m "my work before session X.Y"

# 2. Pull the updates
git pull origin main
```

### Your Customizations Are Safe

Starting in Session 2.1, you will customize your app's appearance (theme, branding, landing page). These files are configured so that **your version is always kept** when you pull updates. You will never get merge conflicts on:

- `.streamlit/config.toml` (your theme colors and fonts)
- `.streamlit/static/` (your logo, images, CSS)
- `student_config.yaml` (your app name and tagline)
- `app/pages/1_Home.py` (your landing page)

This happens automatically — you don't need to do anything special. Just `git pull` and your customizations stay intact while the instructor's backend updates merge in cleanly.

---

## Working in the Repo

### Notebooks (`notebooks/`)

Some sessions use notebooks for exploration. The instructor provides these in `notebooks/`. To work in a notebook:

1. Open the notebook from `notebooks/`
2. Save your own copy to `notebooks/my_work/` if you want to keep your changes
3. Files in `my_work/` are not tracked by git — they're your personal scratch space

### Python Files (`pipeline/`, `app/`)

Most AI-3 work is in `.py` files. You'll code alongside the instructor in class, building modules that become part of your application.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run `uv sync` to install dependencies |
| `AuthenticationError` from Anthropic | Check `ANTHROPIC_API_KEY` in `.env` |
| `AuthenticationError` from Voyage | Check `VOYAGE_API_KEY` in `.env` |
| ChromaDB returns 0 results | Verify `chroma_db/` directory exists and is not empty |
| `git pull` shows merge conflicts | Run `git config merge.ours.driver true` (setup.sh should have done this) |
| Streamlit app won't start | Check that `streamlit` is installed: `uv sync` |
| Python version error | AI-3 requires Python 3.12+. Check with `python --version` |
