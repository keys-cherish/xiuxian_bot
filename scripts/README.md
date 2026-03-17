# Smoke Scripts

**Recommended**
- `smoke_bot_layer.py`: Bot-level integration smoke (simulates Telegram updates, no network).
- `smoke_api_e2e.py`: Core API smoke via Flask test client (no network).
- `smoke_social_chat.py`: 论道精力规则专项验证。

**Quick Regression**
- `pytest -m smoke -q`
- `python scripts/smoke_bot_layer.py`
