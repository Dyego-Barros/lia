import asyncio

from app.infrastructure.events.conversation_events import ConversationEventBroker


def test_broker_delivers_events_to_subscriber():
    async def scenario():
        broker = ConversationEventBroker()
        async for queue in broker.subscribe():
            await broker.publish("conversation-1")
            assert await asyncio.wait_for(queue.get(), timeout=0.1) == "conversation-1"
            break

    asyncio.run(scenario())


def test_broker_keeps_latest_event_for_slow_subscriber():
    async def scenario():
        broker = ConversationEventBroker(queue_size=1)
        async for queue in broker.subscribe():
            await broker.publish("old")
            await broker.publish("new")
            assert await asyncio.wait_for(queue.get(), timeout=0.1) == "new"
            break

    asyncio.run(scenario())
