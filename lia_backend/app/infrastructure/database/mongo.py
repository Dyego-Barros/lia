"""Persistência da inbox de WhatsApp em documentos MongoDB.

Cada conversa é um documento. O array `mensagens` é limitado para evitar o
limite de 16 MB por documento do MongoDB; o limite pode ser ajustado por env.
"""

import os
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from app.infrastructure.events.conversation_events import conversation_events

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
        "foto_perfil": item.get("foto_perfil"),
        "status": item.get("status", "aberta"),
        "ultima_mensagem_em": item["ultima_mensagem_em"],
        "ultima_mensagem_recebida": item.get("ultima_mensagem_recebida"),
        "nao_lidas": item.get("nao_lidas", 0),
        "humano_ate": item.get("humano_ate"),
        "historico_openwa_sincronizado_em": item.get("historico_openwa_sincronizado_em"),
    }


def _message_view(message: dict[str, Any], conversation_id: str) -> dict[str, Any]:
    return {
        "id": message["id"],
        "conversation_id": conversation_id,
        "direcao": message["direcao"],
        "origem": message.get("origem") or ("cliente" if message["direcao"] == "entrada" else "desconhecida"),
        "tipo": message.get("tipo", "text"),
        "conteudo": message["conteudo"],
        "enviado_em": message["enviado_em"],
        "arquivo_nome": message.get("arquivo_nome"),
        "mime_type": message.get("mime_type"),
        "arquivo_url": f"/api/integracoes/conversas/{conversation_id}/mensagens/{message['id']}/arquivo" if message.get("mime_type") else None,
    }


async def list_conversations() -> list[dict[str, Any]]:
    collection = await conversation_collection()
    return [_view(item) async for item in collection.find({}, {"mensagens": 0}).sort("ultima_mensagem_em", -1)]


async def list_conversations_page(page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    collection = await conversation_collection()
    total = await collection.count_documents({})
    cursor = (
        collection.find({}, {"mensagens": 0})
        .sort("ultima_mensagem_em", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return [_view(item) async for item in cursor], total


async def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    collection = await conversation_collection()
    return await collection.find_one({"_id": _object_id(conversation_id)})


async def get_conversation_view(conversation_id: str) -> dict[str, Any] | None:
    collection = await conversation_collection()
    item = await collection.find_one({"_id": _object_id(conversation_id)}, {"mensagens": 0})
    return _view(item) if item else None


async def get_by_identity(integration_id: int, telefone: str) -> dict[str, Any] | None:
    collection = await conversation_collection()
    return await collection.find_one({"integration_id": integration_id, "telefone": telefone})


async def get_active_human_conversation(telefone: str) -> dict[str, Any] | None:
    digits = "".join(character for character in telefone if character.isdigit())
    for conversation in await list_conversations():
        conversation_digits = "".join(character for character in conversation.get("telefone", "") if character.isdigit())
        if conversation_digits != digits or conversation.get("status") != "humano":
            continue
        human_until = conversation.get("humano_ate")
        if human_until and human_until <= datetime.now():
            await update_status(conversation["id"], "aberta")
            continue
        if not human_until:
            await update_status(conversation["id"], "humano")
        return conversation
    return None


async def activate_human_by_phone(telefone: str) -> bool:
    digits = "".join(character for character in telefone if character.isdigit())
    for conversation in await list_conversations():
        conversation_digits = "".join(character for character in conversation.get("telefone", "") if character.isdigit())
        if conversation_digits == digits:
            await update_status(conversation["id"], "humano")
            return True
    return False


async def create_conversation(integration_id: int, telefone: str, nome_contato: str | None = None, chat_id: str | None = None, foto_perfil: str | None = None) -> dict[str, Any]:
    now = datetime.now()
    item = {"integration_id": integration_id, "telefone": telefone, "chat_id": chat_id, "nome_contato": nome_contato, "foto_perfil": foto_perfil, "status": "aberta", "ultima_mensagem_em": now, "nao_lidas": 0, "mensagens": []}
    collection = await conversation_collection()
    result = await collection.insert_one(item)
    item["_id"] = result.inserted_id
    return item


async def update_contact(conversation_id: str, *, nome_contato: str | None = None, chat_id: str | None = None, foto_perfil: str | None = None) -> None:
    updates = {}
    if nome_contato:
        updates["nome_contato"] = nome_contato
    if chat_id:
        updates["chat_id"] = chat_id
    if foto_perfil:
        updates["foto_perfil"] = foto_perfil
    if updates:
        collection = await conversation_collection()
        await collection.update_one({"_id": _object_id(conversation_id)}, {"$set": updates})


async def _promote_message_origin(collection: AsyncIOMotorCollection, conversation_id: str, external_id: str, message: dict[str, Any], origin: str | None) -> dict[str, Any]:
    """Corrige a origem quando o webhook de saída chega antes do envio local."""
    if origin in {"ia", "atendente_plataforma", "sistema"} and message.get("origem") != origin:
        await collection.update_one(
            {"_id": _object_id(conversation_id), "mensagens.external_id": external_id},
            {"$set": {"mensagens.$.origem": origin}},
        )
        message["origem"] = origin
    return message


async def append_message(conversation_id: str, *, direcao: str, conteudo: str, tipo: str = "text", origem: str | None = None, external_id: str | None = None, enviado_em: datetime | None = None, arquivo_nome: str | None = None, mime_type: str | None = None) -> dict[str, Any]:
    message = {"id": str(uuid4()), "direcao": direcao, "origem": origem or ("cliente" if direcao == "entrada" else "sistema"), "tipo": tipo, "conteudo": conteudo, "external_id": external_id, "enviado_em": enviado_em or datetime.now(), "arquivo_nome": arquivo_nome, "mime_type": mime_type}
    collection = await conversation_collection()
    current = await collection.find_one({"_id": _object_id(conversation_id)}, {"status": 1})
    if current is None:
        raise KeyError("Conversa não encontrada")
    if external_id:
        existing = await collection.find_one(
            {"_id": _object_id(conversation_id), "mensagens.external_id": external_id},
            {"mensagens.$": 1},
        )
        if existing and existing.get("mensagens"):
            stored = await _promote_message_origin(collection, conversation_id, external_id, existing["mensagens"][0], origem)
            return _message_view(stored, conversation_id)
    updates: dict[str, Any] = {"ultima_mensagem_em": message["enviado_em"]}
    if current.get("status") != "humano":
        updates["status"] = "aberta"
    if direcao == "entrada":
        updates["ultima_mensagem_recebida"] = message
    operation: dict[str, Any] = {"$push": {"mensagens": {"$each": [message], "$slice": -MONGODB_MAX_MESSAGES}}, "$set": updates}
    if direcao == "entrada":
        operation["$inc"] = {"nao_lidas": 1}
    result = await collection.find_one_and_update(
        {
            "_id": _object_id(conversation_id),
            **({"mensagens.external_id": {"$ne": external_id}} if external_id else {}),
        },
        operation,
        return_document=ReturnDocument.AFTER,
    )
    if result is None and external_id:
        existing = await collection.find_one(
            {"_id": _object_id(conversation_id), "mensagens.external_id": external_id},
            {"mensagens.$": 1},
        )
        if existing and existing.get("mensagens"):
            stored = await _promote_message_origin(collection, conversation_id, external_id, existing["mensagens"][0], origem)
            return _message_view(stored, conversation_id)
    view = _message_view(message, conversation_id)
    await conversation_events.publish(conversation_id)
    return view


async def list_messages(conversation_id: str) -> list[dict[str, Any]]:
    conversation = await get_conversation(conversation_id)
    if conversation is None:
        raise KeyError("Conversa não encontrada")
    return [_message_view(item, conversation_id) for item in conversation.get("mensagens", [])]


async def list_messages_page(conversation_id: str, limit: int, before: datetime | None = None) -> dict[str, Any]:
    """Retorna as mensagens mais recentes sem transportar todo o documento."""
    collection = await conversation_collection()
    condition: dict[str, Any] = {"$lt": ["$$message.enviado_em", before]} if before else {"$literal": True}
    rows = await collection.aggregate([
        {"$match": {"_id": _object_id(conversation_id)}},
        {"$project": {
            "mensagens": {
                "$slice": [
                    {"$filter": {"input": {"$ifNull": ["$mensagens", []]}, "as": "message", "cond": condition}},
                    -(limit + 1),
                ],
            },
        }},
    ]).to_list(length=1)
    if not rows:
        raise KeyError("Conversa não encontrada")
    messages = rows[0].get("mensagens", [])
    has_more = len(messages) > limit
    page = messages[-limit:]
    return {
        "items": [_message_view(item, conversation_id) for item in page],
        "has_more": has_more,
        "next_before": page[0]["enviado_em"].isoformat() if has_more and page else None,
    }


async def get_message(conversation_id: str, message_id: str) -> dict[str, Any] | None:
    conversation = await get_conversation(conversation_id)
    if conversation is None:
        return None
    return next((item for item in conversation.get("mensagens", []) if item.get("id") == message_id), None)


async def mark_read(conversation_id: str) -> None:
    collection = await conversation_collection()
    result = await collection.update_one({"_id": _object_id(conversation_id)}, {"$set": {"nao_lidas": 0}})
    if result.modified_count:
        await conversation_events.publish(conversation_id)


async def unread_summary() -> dict[str, int]:
    collection = await conversation_collection()
    pipeline = [
        {"$match": {"nao_lidas": {"$gt": 0}}},
        {"$group": {"_id": None, "conversas": {"$sum": 1}, "mensagens": {"$sum": "$nao_lidas"}}},
    ]
    result = await collection.aggregate(pipeline).to_list(length=1)
    return result[0] if result else {"conversas": 0, "mensagens": 0}


async def claim_history_sync(conversation_id: str) -> bool:
    """Reserva uma única sincronização, recuperando reservas abandonadas."""
    collection = await conversation_collection()
    stale_before = datetime.now() - timedelta(minutes=15)
    result = await collection.find_one_and_update(
        {
            "_id": _object_id(conversation_id),
            "historico_openwa_sincronizado_em": {"$exists": False},
            "$or": [
                {"historico_openwa_sincronizando_em": {"$exists": False}},
                {"historico_openwa_sincronizando_em": {"$lt": stale_before}},
            ],
        },
        {"$set": {"historico_openwa_sincronizando_em": datetime.now()}},
    )
    return result is not None


async def complete_history_sync(conversation_id: str) -> None:
    collection = await conversation_collection()
    await collection.update_one(
        {"_id": _object_id(conversation_id)},
        {
            "$set": {"historico_openwa_sincronizado_em": datetime.now()},
            "$unset": {"historico_openwa_sincronizando_em": ""},
        },
    )


async def release_history_sync(conversation_id: str) -> None:
    collection = await conversation_collection()
    await collection.update_one(
        {"_id": _object_id(conversation_id)},
        {"$unset": {"historico_openwa_sincronizando_em": ""}},
    )


async def import_messages(conversation_id: str, messages: list[dict[str, Any]]) -> int:
    """Importa histórico sem duplicar e preservando a ordem cronológica."""
    if not messages:
        return 0
    collection = await conversation_collection()
    object_id = _object_id(conversation_id)
    conversation = await collection.find_one({"_id": object_id})
    if conversation is None:
        raise KeyError("Conversa não encontrada")

    existing = conversation.get("mensagens", [])
    external_ids = {item.get("external_id") for item in existing if item.get("external_id")}
    fingerprints = [
        (item.get("direcao"), item.get("conteudo"), item.get("enviado_em"))
        for item in existing
    ]
    imported: list[dict[str, Any]] = []
    for candidate in sorted(messages, key=lambda item: item["enviado_em"]):
        external_id = candidate.get("external_id")
        if external_id and external_id in external_ids:
            continue
        duplicate = any(
            direction == candidate["direcao"]
            and content == candidate["conteudo"]
            and isinstance(sent_at, datetime)
            and abs((sent_at - candidate["enviado_em"]).total_seconds()) <= 120
            for direction, content, sent_at in fingerprints
        )
        if duplicate:
            continue
        message = {
            "id": str(uuid4()),
            "direcao": candidate["direcao"],
            "origem": candidate.get("origem") or ("cliente" if candidate["direcao"] == "entrada" else "atendente_whatsapp"),
            "tipo": candidate.get("tipo", "text"),
            "conteudo": candidate["conteudo"],
            "external_id": external_id,
            "enviado_em": candidate["enviado_em"],
            "arquivo_nome": candidate.get("arquivo_nome"),
            "mime_type": candidate.get("mime_type"),
        }
        imported.append(message)
        fingerprints.append((message["direcao"], message["conteudo"], message["enviado_em"]))
        if external_id:
            external_ids.add(external_id)

    if not imported:
        return 0
    latest = max(item["enviado_em"] for item in imported)
    update: dict[str, Any] = {
        "$push": {"mensagens": {"$each": imported, "$sort": {"enviado_em": 1}, "$slice": -MONGODB_MAX_MESSAGES}},
        "$max": {"ultima_mensagem_em": latest},
    }
    inbound = [item for item in imported if item["direcao"] == "entrada"]
    if inbound:
        newest_inbound = max(inbound, key=lambda item: item["enviado_em"])
        current_inbound = conversation.get("ultima_mensagem_recebida")
        if not current_inbound or current_inbound.get("enviado_em") < newest_inbound["enviado_em"]:
            update["$set"] = {"ultima_mensagem_recebida": newest_inbound}
    await collection.update_one({"_id": object_id}, update)
    await conversation_events.publish(conversation_id)
    return len(imported)


async def update_status(conversation_id: str, status: str) -> dict[str, Any] | None:
    collection = await conversation_collection()
    changes: dict[str, Any] = {"status": status}
    update: dict[str, Any] = {"$set": changes}
    if status == "humano":
        changes["humano_ate"] = datetime.now() + timedelta(hours=24)
    else:
        update["$unset"] = {"humano_ate": ""}
    await collection.update_one({"_id": _object_id(conversation_id)}, update)
    await conversation_events.publish(conversation_id)
    return await get_conversation(conversation_id)


async def close() -> None:
    _client.close()
