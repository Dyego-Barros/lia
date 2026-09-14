"""Canal em memória para notificações em tempo real da inbox.

O MongoDB continua sendo a fonte da verdade. Os eventos apenas avisam os
navegadores conectados de que devem buscar o estado persistido mais recente.
"""

import asyncio
from collections.abc import AsyncIterator


class ConversationEventBroker:
    def __init__(self, queue_size: int = 32) -> None:
        self._queue_size = queue_size
        self._subscribers: set[asyncio.Queue[str]] = set()

    async def publish(self, conversation_id: str) -> None:
        for queue in tuple(self._subscribers):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(conversation_id)

    async def subscribe(self) -> AsyncIterator[asyncio.Queue[str]]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=self._queue_size)
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)


conversation_events = ConversationEventBroker()
