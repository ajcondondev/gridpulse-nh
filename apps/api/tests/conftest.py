import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path():
    base_dir = Path(__file__).resolve().parents[3] / "data" / "test_tmp"
    base_dir.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(dir=base_dir))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
