from __future__ import annotations

import json
import os
from typing import Any


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _read_users() -> dict[str, Any]:
    _ensure_data_dir()
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _write_users(data: dict[str, Any]) -> None:
    _ensure_data_dir()
    tmp_file = USERS_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, USERS_FILE)


def _ensure_user_defaults(user: dict[str, Any], default_topics: list[str]) -> dict[str, Any]:
    # topics
    if not user.get("topics"):
        user["topics"] = default_topics
    # settings
    settings = user.get("settings", {})
    settings.setdefault("latest_count", 3)
    settings.setdefault("daily_count", 5)
    settings.setdefault("schedule", "morning")  # morning|evening|night
    settings.setdefault("subscribed", False)
    user["settings"] = settings
    return user


def get_user_topics(user_id: int, default_topics: list[str]) -> list[str]:
    data = _read_users()
    key = str(user_id)
    user = _ensure_user_defaults(data.get(key, {}), default_topics)
    topics = user.get("topics", default_topics)
    data[key] = user
    _write_users(data)
    return topics


def set_user_topics(user_id: int, topics: list[str]) -> None:
    data = _read_users()
    key = str(user_id)
    user = data.get(key, {})
    user.setdefault("settings", {})
    user["topics"] = topics
    data[key] = user
    _write_users(data)


def get_user_settings(user_id: int, default_topics: list[str]) -> dict[str, Any]:
    data = _read_users()
    key = str(user_id)
    user = _ensure_user_defaults(data.get(key, {}), default_topics)
    data[key] = user
    _write_users(data)
    return user["settings"]


def update_user_settings(user_id: int, **kwargs: Any) -> dict[str, Any]:
    data = _read_users()
    key = str(user_id)
    user = data.get(key, {"topics": [], "settings": {}})
    settings = user.get("settings", {})
    settings.update({k: v for k, v in kwargs.items() if v is not None})
    user["settings"] = settings
    data[key] = user
    _write_users(data)
    return settings

