from __future__ import annotations

from pathlib import Path

import pytest

from simulacion.config import ModeloConfig, cargar_config

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def config_original() -> ModeloConfig:
    return cargar_config(RAIZ / "configs" / "original.toml")
