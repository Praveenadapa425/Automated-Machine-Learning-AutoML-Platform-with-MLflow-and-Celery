import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_sys_path(monkeypatch, tmp_path):
    """Ensure tests import the correct `app` package by temporarily adjusting sys.path.

This fixture makes a best-effort attempt to isolate imports by prepending local
`api/` or `worker/app/` paths when tests import modules. Tests should still
explicitly insert the intended path if they need the worker package.
"""
    # Ensure tests run from project root
    repo_root = Path(__file__).resolve().parents[1]
    # Prepend repo root so imports relying on relative paths work
    monkeypatch.syspath_prepend(str(repo_root))
    # Provide default env dirs inside tmp_path
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "reports"))
    (tmp_path / "uploads").mkdir()
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "reports").mkdir()
    yield
