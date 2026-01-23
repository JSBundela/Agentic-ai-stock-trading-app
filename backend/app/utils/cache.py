"""Simple module-level session cache using global variables with file persistence."""

import json
import os
from typing import Optional

# Session file path
SESSION_FILE = "session_cache.json"

# Module-level variables - persist for the lifetime of the process
_view_token: str | None = None
_view_sid: str | None = None
_trade_token: str | None = None
_trade_sid: str | None = None
_base_url: str | None = None
_data_center: str | None = None


def _load_from_file():
    """Load session from persistent file if it exists."""
    global _view_token, _view_sid, _trade_token, _trade_sid, _base_url, _data_center
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
                _view_token = data.get('view_token')
                _view_sid = data.get('view_sid')
                _trade_token = data.get('trade_token')
                _trade_sid = data.get('trade_sid')
                _base_url = data.get('base_url')
                _data_center = data.get('data_center')
                print(f"💎💎💎 [CACHE] LOADED: trade_token={'YES' if _trade_token else 'NO'}, sid={'YES' if _trade_sid else 'NO'}")
                if _trade_token:
                    print(f"💎💎💎 [CACHE] TOKEN SAMPLE: {_trade_token[:10]}...")
        except Exception as e:
            print(f"❌ [CACHE] Failed to load session file: {e}")


def _save_to_file():
    """Save current session to persistent file."""
    try:
        data = {
            'view_token': _view_token,
            'view_sid': _view_sid,
            'trade_token': _trade_token,
            'trade_sid': _trade_sid,
            'base_url': _base_url,
            'data_center': _data_center
        }
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[CACHE] Failed to save session file: {e}")


# Load existing session on module import
_load_from_file()


def set_view_session(view_token: str, view_sid: str):
    global _view_token, _view_sid
    _view_token = view_token
    _view_sid = view_sid
    _save_to_file()
    print(f"[CACHE] View session saved")


def get_view_session() -> tuple[str | None, str | None]:
    return _view_token, _view_sid


def set_trade_session(trade_token: str, trade_sid: str, base_url: str = None, data_center: str = None):
    global _trade_token, _trade_sid, _base_url, _data_center
    _trade_token = trade_token
    _trade_sid = trade_sid
    _base_url = base_url
    _data_center = data_center
    _save_to_file()
    print(f"[CACHE] Trade session saved. Base URL: {base_url}")


def get_trade_session() -> tuple[str | None, str | None, str | None, str | None]:
    return _trade_token, _trade_sid, _base_url, _data_center


def clear_cache():
    global _view_token, _view_sid, _trade_token, _trade_sid, _base_url, _data_center
    _view_token = None
    _view_sid = None
    _trade_token = None
    _trade_sid = None
    _base_url = None
    _data_center = None
    _save_to_file()
    print("[CACHE] Session cleared")


def has_view_session() -> bool:
    """Check if view session exists (for debug logging)."""
    return _view_token is not None and _view_sid is not None
