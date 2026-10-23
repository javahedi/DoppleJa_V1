"""Single-process WebSocket delivery for matched DoppleJa users.

PostgreSQL remains authoritative. For multiple API workers/containers,
replace this in-memory hub with Redis pub/sub before scaling.
"""
import asyncio
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from backend.app.core.database import SessionLocal
from backend.app.models import Message, User
from backend.app.modules.auth.security import COOKIE_NAME, read_session
from backend.app.modules.chat.router import require_match
from backend.app.modules.chat.schemas import MessageCreate, MessageOut

router = APIRouter(tags=["Chat WebSocket"])


@dataclass(eq=False)
class Subscriber:
    loop: asyncio.AbstractEventLoop
    queue: asyncio.Queue


class ChatHub:
    def __init__(self):
        self._listeners: dict[UUID, set[Subscriber]] = defaultdict(set)

    def subscribe(self, match_id: UUID) -> Subscriber:
        subscriber = Subscriber(asyncio.get_running_loop(), asyncio.Queue(maxsize=100))
        self._listeners[match_id].add(subscriber)
        return subscriber

    def unsubscribe(self, match_id: UUID, subscriber: Subscriber) -> None:
        subscribers = self._listeners.get(match_id)
        if subscribers is not None:
            subscribers.discard(subscriber)
            if not subscribers:
                self._listeners.pop(match_id, None)

    def publish(self, match_id: UUID, payload: dict) -> None:
        # Called from FastAPI sync REST endpoints in the threadpool, too.
        for subscriber in tuple(self._listeners.get(match_id, ())):
            def deliver(sub=subscriber):
                if sub.queue.full():
                    # Slow clients can retrieve authoritative history via REST.
                    self.unsubscribe(match_id, sub)
                    return
                sub.queue.put_nowait(payload)
            subscriber.loop.call_soon_threadsafe(deliver)


hub = ChatHub()


def verified_participant(match_id: UUID, token: str | None) -> UUID | None:
    user_id = read_session(token) if token else None
    if user_id is None:
        return None
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if not user or not user.is_active or user.email_verified_at is None:
            return None
        try:
            require_match(db, match_id, user)
        except Exception:
            return None
    return user_id


def store_message(match_id: UUID, user_id: UUID, content: str) -> dict:
    # Re-check permissions before each write, not only at connection time.
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if not user or not user.is_active or user.email_verified_at is None:
            raise PermissionError("Session no longer valid")
        try:
            require_match(db, match_id, user)
        except Exception as exc:
            raise PermissionError("Match no longer accessible") from exc
        item = Message(match_id=match_id, sender_id=user_id, content=content)
        db.add(item)
        db.commit()
        db.refresh(item)
        return MessageOut.model_validate(item).model_dump(mode="json")


async def writer(ws: WebSocket, sub: Subscriber):
    while True:
        await ws.send_json(await sub.queue.get())


@router.websocket('/ws/matches/{match_id}')
async def websocket_chat(ws: WebSocket, match_id: UUID):
    allowed = set(os.getenv('WS_ALLOWED_ORIGINS', 'http://127.0.0.1:8001,http://localhost:8001').split(','))
    origin = ws.headers.get('origin')
    if origin is not None and origin not in allowed:
        await ws.close(code=1008)
        return
    token = ws.cookies.get(COOKIE_NAME)
    user_id = await run_in_threadpool(verified_participant, match_id, token)
    if user_id is None:
        await ws.close(code=1008)
        return

    await ws.accept()
    sub = hub.subscribe(match_id)
    write_task = asyncio.create_task(writer(ws, sub))
    try:
        while True:
            try:
                text = await ws.receive_text()
                payload = json.loads(text)
                if not isinstance(payload, dict) or payload.get('type') != 'message':
                    raise ValueError('Expected {"type":"message","content":"..."}')
                validated = MessageCreate.model_validate({'content': payload.get('content')})
            except (ValueError, ValidationError, TypeError):
                await ws.send_json({'type': 'error', 'detail': 'Invalid message (1–2000 characters)'})
                continue
            try:
                saved = await run_in_threadpool(store_message, match_id, user_id, validated.content)
            except PermissionError:
                await ws.close(code=1008)
                break
            hub.publish(match_id, {'type': 'message', 'message': saved})
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(match_id, sub)
        write_task.cancel()
        await asyncio.gather(write_task, return_exceptions=True)
