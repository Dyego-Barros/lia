"""Persistência da inbox de WhatsApp em documentos MongoDB.

Cada conversa é um documento. O array `mensagens` é limitado para evitar o
limite de 16 MB por documento do MongoDB; o limite pode ser ajustado por env.
"""

import os
from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import ReturnDocument


MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "lash")
MONGODB_MAX_MESSAGES = int(os.getenv("MONGODB_MAX_MESSAGES", "2000"))

_client = AsyncIOMotorClient(MONGODB_URL)
_collection: AsyncIOMotorCollection | None = None
_indexes_ready = False


async def conversation_collection() -> AsyncIOMotorCollection:
    global _collection, _indexes_ready
    if _collection is None:
        _collection = _client[MONGODB_DATABASE]["whatsapp_conversations"]
    if not _indexes_ready:
        await _collection.create_index([("integration_id", 1), ("telefone", 1)], unique=True, name="conversation_identity")
        await _collection.create_index([("ultima_mensagem_em", -1)], name="conversation_last_message")
        _indexes_ready = True
    return _collection


def _object_id(conversation_id: str) -> ObjectId:
    if not ObjectId.is_valid(conversation_id):
        raise ValueError("ID de conversa inválido")
    return ObjectId(conversation_id)


def _view(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item["_id"]),
        "integration_id": item["integration_id"],
        "telefone": item["telefone"],
        "chat_id": item.get("chat_id"),
        "nome_contato": item.get("nome_contato"),
        "status": item.get("status", "aberta"),
        "ultima_mensagem_em": item["ultima_mensagem_em"],
        "ultima_mensagem_recebida": item.get("ultima_mensagem_recebida"),
    }


def _message_view(message: dict[str, Any], conversation_id: str) -> dict[str, Any]:
    return {
        "id": message["id"],
        "conversation_id": conversation_id,
        "direcao": message["direcao"],
        "tipo": message.get("tipo", "text"),
        "conteudo": message["conteudo"],
        "enviado_em": message["enviado_em"],
    }


async def list_conversations() -> list[dict[str, Any]]:
    collection = await conversation_collection()
    return [_view(item) async for item in collection.find({}, {"mensagens": 0}).sort("ultima_mensagem_em", -1)]


async def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    collection = await conversation_collection()
    return await collection.find_one({"_id": _object_id(conversation_id)})


async def get_by_identity(integration_id: int, telefone: str) -> dict[str, Any] | None:
    collection = await conversation_collection()
    return await collection.find_one({"integration_id": integration_id, "telefone": telefone})


async def create_conversation(integration_id: int, telefone: str, nome_contato: str | None = None, chat_id: str | None = None) -> dict[str, Any]:
    now = datetime.now()
    item = {"integration_id": integration_id, "telefone": telefone, "chat_id": chat_id, "nome_contato": nome_contato, "status": "aberta", "ultima_mensagem_em": now, "mensagens": []}
    collection = await conversation_collection()
    result = await collection.insert_one(item)
    item["_id"] = result.inserted_id
    return item


async def update_contact(conversation_id: str, *, nome_contato: str | None = None, chat_id: str | None = None) -> None:
    updates = {}
    if nome_contato:
        updates["nome_contato"] = nome_contato
    if chat_id:
        updates["chat_id"] = chat_id
    if updates:
        collection = await conversation_collection()
        await collection.update_one({"_id": _object_id(conversation_id)}, {"$set": updates})


async def append_message(conversation_id: str, *, direcao: str, conteudo: str, tipo: str = "text", external_id: str | None = None, enviado_em: datetime | None = None) -> dict[str, Any]:
    message = {"id": str(uuid4()), "direcao": direcao, "tipo": tipo, "conteudo": conteudo, "external_id": external_id, "enviado_em": enviado_em or datetime.now()}
    collection = await conversation_collection()
    updates: dict[str, Any] = {"ultima_mensagem_em": message["enviado_em"], "status": "aberta"}
    if direcao == "entrada":
        updates["ultima_mensagem_recebida"] = message
    result = await collection.find_one_and_update(
        {"_id": _object_id(conversation_id)},
        {"$push": {"mensagens": {"$each": [message], "$slice": -MONGODB_MAX_MESSAGES}}, "$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise KeyError("Conversa não encontrada")
    return _message_view(message, conversation_id)


async def list_messages(conversation_id: str) -> list[dict[str, Any]]:
    conversation = await get_conversation(conversation_id)
    if conversation is None:
        raise KeyError("Conversa não encontrada")
    return [_message_view(item, conversation_id) for item in conversation.get("mensagens", [])]


async def update_status(conversation_id: str, status: str) -> dict[str, Any] | None:
    collection = await conversation_collection()
    await collection.update_one({"_id": _object_id(conversation_id)}, {"$set": {"status": status}})
    return await get_conversation(conversation_id)


async def close() -> None:
    _client.close()
