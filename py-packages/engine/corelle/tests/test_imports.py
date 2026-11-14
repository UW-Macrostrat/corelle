import subprocess
import sys
from os import environ


def test_engine_import_has_no_side_effects(tmp_path):
    """Libraries such as the Macrostrat CLI import the engine directly."""
    (tmp_path / ".env").write_text("CORELLE_IMPORT_SENTINEL=1\n")
    code = (
        "import os, warnings\n"
        "before = list(warnings.filters)\n"
        "import corelle.engine\n"
        "assert 'CORELLE_IMPORT_SENTINEL' not in os.environ, 'read .env'\n"
        "assert warnings.filters == before, 'changed warning filters'\n"
    )
    env = {k: v for k, v in environ.items() if k != "CORELLE_IMPORT_SENTINEL"}
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, env=env, capture_output=True
    )
    assert result.returncode == 0, result.stderr.decode()


def test_engine_imports_without_a_database():
    """API v3 builds its app at import, before any database is reachable."""
    code = (
        "import corelle.engine.rotate, corelle.engine.cache, corelle.engine.storage\n"
        "import corelle.engine.database\n"
    )
    env = dict(environ, CORELLE_DB="postgresql://nobody@invalid.invalid:1/none")
    result = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, timeout=60
    )
    assert result.returncode == 0, result.stderr.decode()
