# Northbrook Q&A -- Claude Code Instructions

## Files You Own (safe to modify)
- `.streamlit/config.toml` -- Theme colors, font
- `.streamlit/static/` -- Logo images, any static assets
- `student_config.yaml` -- App name, tagline, welcome message
- `app/branding.py` -- Logo placement, CSS styling, favicon, page config

## Files You Should NOT Modify
- `app/main.py` -- Chat infrastructure (instructor-managed)
- `app/rag.py` -- Pipeline integration (instructor-managed; main.py imports from this — that's expected)
- `pipeline/` -- Backend retrieval pipeline (instructor-managed)
- `data/` -- Northbrook corpus (instructor-managed)
- `scripts/` -- Setup and evaluation scripts (instructor-managed)
- `notebooks/` -- Session notebooks (instructor-managed)
- `.env` -- API keys (never commit)

## Important Rules
- In `app/branding.py`, `st.set_page_config()` MUST remain the first `st.*` call. Do not add any Streamlit commands above it.
- In `student_config.yaml`, always wrap string values in double quotes (e.g., `app_name: "My App"`) to avoid YAML parsing issues with colons, #, or special characters.
- Do not modify `app/rag.py` -- it contains the RAG pipeline integration and is updated by the instructor between sessions.

## Streamlit Theming Reference
Available keys in `.streamlit/config.toml` under `[theme]`:
- `primaryColor` -- Accent color for interactive elements
- `backgroundColor` -- Main content area background
- `secondaryBackgroundColor` -- Sidebar and widget background
- `textColor` -- Main text color
- `font` -- "sans serif", "serif", or "monospace"

## Example Prompts
- "Change the app name to 'My AI Assistant' and update the tagline"
- "Set a dark theme with blue accents"
- "Add my logo from .streamlit/static/logo.png to the sidebar"
- "Create a professional welcome message with 3 example questions"
- "Add custom CSS to style the chat bubbles"
