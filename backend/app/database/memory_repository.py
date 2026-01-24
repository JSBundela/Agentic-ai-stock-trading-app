from app.database import get_db
from app.core.logger import logger
from typing import List, Dict, Any

class MemoryRepository:
    async def add_message(self, session_id: str, role: str, content: str, agent_name: str = None):
        """Save a message to the agent memory."""
        try:
            db = await get_db()
            await db.execute(
                """
                INSERT INTO agent_memory (session_id, role, content, agent_name)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, agent_name)
            )
            await db.commit()
            logger.info(f"Saved memory for session {session_id}: {role} ({agent_name})")
        except Exception as e:
            logger.error(f"Failed to save agent memory: {e}")

    async def get_session_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent chat history for a session."""
        try:
            db = await get_db()
            async with db.execute(
                """
                SELECT role, content, agent_name, timestamp 
                FROM agent_memory 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """,
                (session_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                
                # Reverse to return in chronological order (oldest first)
                history = [
                    {
                        "role": row[0],
                        "content": row[1],
                        "agent_name": row[2],
                        "timestamp": row[3]
                    }
                    for row in rows
                ]
                return history[::-1]
        except Exception as e:
            logger.error(f"Failed to retrieve agent memory: {e}")
            return []

memory_repository = MemoryRepository()
