# FARS Paper Knowledge Layer

This repository contains the first implementation milestone for FARS: a paper knowledge layer that ingests scholarly metadata, stores structured paper records, preserves citation relationships, and exposes API endpoints that future research agents can build on.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Run the API

```bash
uvicorn fars_kg.api.app:app --reload
```
