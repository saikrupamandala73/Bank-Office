import os
import tempfile
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.gettempdir(), "backend_pytest.db").replace("\\", "/")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import Base, engine
import seed


@pytest.fixture
def client():
    seed.reset_and_seed()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def empty_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
