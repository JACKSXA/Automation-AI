"""
Command handler — processes incoming owner messages (slash-commands and chat).
Called from the supervisor main loop in server.py.

Extracted from server.py to keep server.py focused on HTTP/WebSocket routing.
"""

import logging
import threading
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger("supervisor.command_handler")


def handle_message(text: str, chat_id: int, user_id: int, ctx: Any) -> None:
    """Process a single incoming owner message.

    ctx is the _event_ctx SimpleNamespace from _run_supervisor. It must expose:
        send_with_budget, load_state, save_state, safe_restart, kill_workers,
        queue_review_task, persist_queue_snapshot, sort_pending, PENDING,
        consciousness, request_restart, soft_timeout, hard_timeout.
    """
    from supervisor.message_bus import log_chat
    from supervisor.state import status_text

    now_iso = datetime.now(timezone.utc).isoformat()
    st = ctx.load_state()
    if st.get("owner_id") is None:
        st["owner_id"] = user_id
        st["owner_chat_id"] = chat_id
    log_chat("in", chat_id, user_id, text)
    st["last_owner_message_at"] = now_iso
    ctx.save_state(st)

    if not text:
        return

    lowered = text.strip().lower()

    if lowered.startswith("/panic"):
        ctx.send_with_budget(chat_id, "🛑 PANIC: killing everything. App will close.")
        ctx.execute_panic()

    elif lowered.startswith("/restart"):
        ctx.send_with_budget(chat_id, "♻️ Restarting (soft).")
        ok, restart_msg = ctx.safe_restart(
            reason="owner_restart", unsynced_policy="rescue_and_reset"
        )
        if not ok:
            ctx.send_with_budget(chat_id, f"⚠️ Restart cancelled: {restart_msg}")
            return
        ctx.kill_workers()
        ctx.request_restart()

    elif lowered.startswith("/review"):
        ctx.queue_review_task(reason="owner:/review", force=True)

    elif lowered.startswith("/evolve"):
        parts = lowered.split()
        action = parts[1] if len(parts) > 1 else "on"
        turn_on = action not in ("off", "stop", "0")
        st2 = ctx.load_state()
        st2["evolution_mode_enabled"] = bool(turn_on)
        if turn_on:
            st2["evolution_consecutive_failures"] = 0
        ctx.save_state(st2)
        if not turn_on:
            ctx.PENDING[:] = [t for t in ctx.PENDING if str(t.get("type")) != "evolution"]
            ctx.sort_pending()
            ctx.persist_queue_snapshot(reason="evolve_off")
        ctx.send_with_budget(chat_id, f"🧬 Evolution: {'ON' if turn_on else 'OFF'}")

    elif lowered.startswith("/bg"):
        parts = lowered.split()
        action = parts[1] if len(parts) > 1 else "status"
        if action in ("start", "on", "1"):
            result = ctx.consciousness.start()
            _bg_s = ctx.load_state()
            _bg_s["bg_consciousness_enabled"] = True
            ctx.save_state(_bg_s)
            ctx.send_with_budget(chat_id, f"🧠 {result}")
        elif action in ("stop", "off", "0"):
            result = ctx.consciousness.stop()
            _bg_s = ctx.load_state()
            _bg_s["bg_consciousness_enabled"] = False
            ctx.save_state(_bg_s)
            ctx.send_with_budget(chat_id, f"🧠 {result}")
        else:
            bg_status = "running" if ctx.consciousness.is_running else "stopped"
            ctx.send_with_budget(chat_id, f"🧠 Background consciousness: {bg_status}")

    elif lowered.startswith("/status"):
        status = status_text(
            ctx.WORKERS, ctx.PENDING, ctx.RUNNING,
            ctx.soft_timeout, ctx.hard_timeout,
        )
        ctx.send_with_budget(chat_id, status, force_budget=True)

    else:
        from supervisor.workers import _get_chat_agent, handle_chat_direct
        ctx.consciousness.inject_observation(f"Owner message: {text[:100]}")
        agent = _get_chat_agent()
        if agent._busy:
            agent.inject_message(text)
        else:
            ctx.consciousness.pause()

            def _run_and_resume(cid: int, txt: str) -> None:
                try:
                    handle_chat_direct(cid, txt, None)
                finally:
                    ctx.consciousness.resume()

            threading.Thread(
                target=_run_and_resume, args=(chat_id, text), daemon=True
            ).start()
