"""Copia o histórico existente do PostgreSQL para a inbox MongoDB.

Execute uma vez antes de colocar a aplicação na versão que grava somente no
MongoDB: `python scripts/migrate_whatsapp_to_mongodb.py`.
"""

import asyncio

from sqlalchemy import select

from app.infrastructure.database.db import AsyncSessionLocal
from app.infrastructure.database.models.models import WhatsAppConversationModel, WhatsAppMessageModel
from app.infrastructure.database import mongo


async def migrate() -> None:
    copied_conversations = 0
    copied_messages = 0
    async with AsyncSessionLocal() as session:
        conversations = (await session.execute(select(WhatsAppConversationModel))).scalars().all()
        for legacy in conversations:
            current = await mongo.get_by_identity(legacy.integration_id, legacy.telefone)
            if current is None:
                current = await mongo.create_conversation(legacy.integration_id, legacy.telefone, legacy.nome_contato)
                copied_conversations += 1
            else:
                continue
            current_id = str(current["_id"])
            messages = (await session.execute(select(WhatsAppMessageModel).where(WhatsAppMessageModel.conversation_id == legacy.id).order_by(WhatsAppMessageModel.enviado_em))).scalars().all()
            for message in messages:
                await mongo.append_message(current_id, direcao=message.direcao, tipo=message.tipo, conteudo=message.conteudo, external_id=message.external_id, enviado_em=message.enviado_em)
                copied_messages += 1
            await (await mongo.conversation_collection()).update_one({"_id": current["_id"]}, {"$set": {"status": legacy.status, "ultima_mensagem_em": legacy.ultima_mensagem_em}})
    print(f"Conversas copiadas: {copied_conversations}; mensagens copiadas: {copied_messages}")


if __name__ == "__main__":
    asyncio.run(migrate())
