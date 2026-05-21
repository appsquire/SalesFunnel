import json
from typing import Any

import yaml

from app.settings import settings

_cache: dict[str, Any] | None = None


def load_funnel_config() -> dict[str, Any]:
    global _cache
    if _cache is None:
        path = settings.resolved_funnel_config()
        with path.open(encoding="utf-8") as f:
            _cache = yaml.safe_load(f)
    return _cache
