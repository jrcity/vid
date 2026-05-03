import os
from pathlib import Path

# Force mock Nokia NaC behavior for local test execution.
# Tests should never depend on external Nokia CAMARA network services.
os.environ['NOKIA_NAC_TOKEN'] = ''
os.environ['APP_ENV'] = 'test'

from app.core.config import get_settings
from app.services import store

settings = get_settings()


def pytest_runtest_setup(item):
    db_path = Path(settings.certificate_store_path)
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    store._phone_index.clear()
    store.initialize_store()
