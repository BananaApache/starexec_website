# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StarExecMiami Website is a Django-based gateway/middleware application that provides a modern web interface to the StarExec platform (a Java-based solver execution system at `https://starexec.acorn.miami.edu`). It proxies authentication and API calls to StarExec, presenting hierarchical space data through a reactive UI.

## Commands

```bash
# Run development server
python manage.py runserver

# Lint and format (uses ruff)
ruff check .
ruff format .

# Run tests
python manage.py test

# Database
python manage.py migrate
python manage.py makemigrations

# Production server
gunicorn project_settings.wsgi:application
```

Package management uses `uv` (see `uv.lock`).

## Architecture

**Two-layer structure:**
- `project_settings/` — Django project config (settings, root URLs, wsgi/asgi)
- `project_website/` — Single Django app containing all application logic

**Core files:**
- `project_website/views.py` — All business logic (~484 lines of functional code)
- `project_website/urls.py` — All app routes
- `project_website/templates/` — 2 main templates + `includes/space_node.html`

### Key Patterns

**Proxy/Gateway Pattern:** Django sits between users and StarExec. Authentication proxies to StarExec's `j_security_check` endpoint; the resulting `JSESSIONID` Java session cookie is stored in Django's session and forwarded on subsequent API calls.

**Lazy Loading via AJAX:** The main dashboard (`home/`) renders an initial space tree, then `space-content/` is an AJAX endpoint that fetches jobs, solvers, benchmarks, users, or subspaces on demand. Frontend uses `<details>` elements + AJAX POST forms.

**Recursive Space Tree:** `build_space_tree()` in views.py recursively fetches subspaces. `includes/space_node.html` is the reusable recursive template component for rendering each tree node.

**File Downloads:** `download/space/<id>/` and `download/xml/<id>/` stream ZIP and XML files from StarExec to the client.

**`proxy/` endpoint:** Fetches StarExec detail pages server-side (CORS bypass), rewrites relative URLs for embedded display.

### Frontend

- Tailwind CSS (CDN), Font Awesome 6, Google Fonts (Inter)
- No build step — Tailwind loaded from CDN
- Templates use Django template language (not Jinja2)

### Environment Variables (`.env`)

```
DJANGO_SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://*.railway.app
j_username=...   # StarExec credentials
j_password=...
```

### Database

SQLite for local dev (`db.sqlite3`). No custom models — only Django's built-in auth tables are used.
