#!/bin/bash
# uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000