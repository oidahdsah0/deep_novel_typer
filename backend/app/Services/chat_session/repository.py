from __future__ import annotations

from app.Schemas.chat import ChatMessage
from app.Schemas.chat_session import (
    ChatSessionSummary,
    CreateChatSessionRequest,
    UpdateChatSessionRequest,
)
from app.Utils.db import AsyncDatabase


class ChatSessionRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self._db = db

    async def list_sessions(self, project_id: str) -> list[ChatSessionSummary]:
        rows = await self._db.fetch_all(
            """
            SELECT id, project_id, title, created_at, updated_at
            FROM chat_sessions
            WHERE project_id = ?
            ORDER BY updated_at DESC
            """,
            (project_id,),
        )
        return [_session_from_row(row) for row in rows]

    async def get_session_row(
        self, project_id: str, session_id: str
    ) -> dict[str, object] | None:
        return await self._db.fetch_one(
            """
            SELECT id, project_id, title, created_at, updated_at
            FROM chat_sessions
            WHERE project_id = ? AND id = ?
            """,
            (project_id, session_id),
        )

    async def create_session(
        self, project_id: str, session_id: str, request: CreateChatSessionRequest, now: str
    ) -> None:
        await self._db.execute(
            """
            INSERT INTO chat_sessions (id, project_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, project_id, request.title, now, now),
        )

    async def update_session(
        self, project_id: str, session_id: str, request: UpdateChatSessionRequest, now: str
    ) -> None:
        await self._db.execute(
            """
            UPDATE chat_sessions SET title = ?, updated_at = ?
            WHERE project_id = ? AND id = ?
            """,
            (request.title, now, project_id, session_id),
        )

    async def delete_session(self, project_id: str, session_id: str) -> None:
        await self._db.execute(
            "DELETE FROM chat_sessions WHERE project_id = ? AND id = ?",
            (project_id, session_id),
        )

    async def list_messages(
        self, project_id: str, session_id: str
    ) -> list[ChatMessage]:
        rows = await self._db.fetch_all(
            """
            SELECT role, content, reasoning
            FROM chat_messages
            WHERE project_id = ? AND session_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (project_id, session_id),
        )
        return [_message_from_row(row) for row in rows]

    async def append_message(
        self, project_id: str, session_id: str, role: str, content: str, reasoning: str, now: str
    ) -> None:
        await self._db.execute(
            """
            INSERT INTO chat_messages (project_id, session_id, role, content, reasoning, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, session_id, role, content, reasoning, now),
        )

    async def persist_turn(
        self,
        project_id: str,
        session_id: str,
        user_content: str,
        assistant_content: str,
        assistant_reasoning: str,
        now: str,
    ) -> None:
        async with self._db.transaction() as conn:
            await conn.execute(
                """
                INSERT INTO chat_messages (project_id, session_id, role, content, reasoning, created_at)
                VALUES (?, ?, 'user', ?, '', ?)
                """,
                (project_id, session_id, user_content, now),
            )
            if assistant_content or assistant_reasoning:
                await conn.execute(
                    """
                    INSERT INTO chat_messages (project_id, session_id, role, content, reasoning, created_at)
                    VALUES (?, ?, 'assistant', ?, ?, ?)
                    """,
                    (
                        project_id,
                        session_id,
                        assistant_content,
                        assistant_reasoning,
                        now,
                    ),
                )
            await conn.execute(
                """
                UPDATE chat_sessions SET updated_at = ?
                WHERE project_id = ? AND id = ?
                """,
                (now, project_id, session_id),
            )


def _session_from_row(row: dict[str, object]) -> ChatSessionSummary:
    return ChatSessionSummary(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        title=str(row["title"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _message_from_row(row: dict[str, object]) -> ChatMessage:
    return ChatMessage(
        role=str(row["role"]),  # type: ignore[arg-type]
        content=str(row["content"]),
        reasoning=str(row["reasoning"] or ""),
    )
