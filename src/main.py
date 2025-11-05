from __future__ import annotations

import asyncio

from .config import TELEGRAM_BOT_TOKEN
from .bot import build_application


async def run() -> None:
    app = build_application(TELEGRAM_BOT_TOKEN)
    await app.initialize()
    try:
        await app.start()
        await app.updater.start_polling()
        # Re-schedule jobs for users who are already subscribed (best-effort, simple scan)
        try:
            # Load users and schedule if subscribed
            from .storage import _read_users  # type: ignore
            from .bot import _schedule_user_job  # type: ignore
            users = _read_users()
            for key, user in users.items():
                settings = user.get("settings", {})
                if settings.get("subscribed"):
                    _schedule_user_job(app, int(key), settings.get("schedule", "morning"))
        except Exception:
            pass
        # Run until Ctrl+C
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass

