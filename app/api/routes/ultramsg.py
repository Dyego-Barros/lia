import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_agent
from app.api.routes.dependencies import (
    agendamento_repository,
    cliente_repository,
    procedimento_repository,
    tempo_trabalho_repository,
)
from app.infrastructure.database.db import get_session
from app.application.services.atendimento_service import AtendimentoService
from app.infrastructure.repositories.repositorie_agendamento import AgendamentoRepository
from app.infrastructure.repositories.repositorie_cliente import ClienteRepository
from app.infrastructure.repositories.repositorie_procedimento import ProcedimentoRepository
from app.infrastructure.repositories.repositorie_tempo_trabalho import TempoTrabalhoRepository
from app.infrastructure.database.models.models import ProcessedWebhookMessageModel

router = APIRouter(prefix="/webhooks/ultramsg", tags=["UltraMsg"])
logger = logging.getLogger(__name__)
PROVIDER = "ultramsg"


def _setting(name: str) -> str:
    return os.getenv(name, "").strip()


def _webhook_secret() -> str:
    return _setting("ULTRAMSG_WEBHOOK_SECRET")


def _extract_message(payload: dict[str, Any]) -> tuple[str, str] | None:
    event_type = payload.get("event_type")
    data = payload.get("data") or {}
    if event_type != "message_received":
        logger.info(
            "Webhook UltraMsg ignorado: event_type=%r data_keys=%s",
            event_type,
            sorted(data.keys()) if isinstance(data, dict) else [],
        )
        return None
    if data.get("fromMe"):
        logger.info(
            "Webhook UltraMsg ignorado: fromMe=%r type=%r data_id=%r "
            "body_present=%s caption_present=%s media_present=%s",
            data.get("fromMe"),
            data.get("type"),
            data.get("id"),
            bool(data.get("body")),
            bool(data.get("caption")),
            bool(data.get("media")),
        )
        return None
    sender = str(data.get("from", "")).split("@", 1)[0]
    body = str(data.get("body", "")).strip()
    if data.get("type") != "chat" and body:
        logger.info(
            "Webhook UltraMsg aceito com tipo=%r porque possui texto; data_id=%r",
            data.get("type"),
            data.get("id"),
        )
    if not sender or not body:
        logger.info(
            "Webhook UltraMsg ignorado: sender_present=%s body_present=%s",
            bool(sender),
            bool(body),
        )
        return None
    return sender, body


async def _send_message(to: str, body: str) -> None:
    instance_id = _setting("ULTRAMSG_INSTANCE_ID")
    token = _setting("ULTRAMSG_TOKEN")
    if not instance_id or not token:
        raise RuntimeError("ULTRAMSG_INSTANCE_ID e ULTRAMSG_TOKEN precisam estar configurados")

    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            url,
            data={"token": token, "to": to, "body": body},
        )
    response.raise_for_status()
    logger.info("Resposta enviada pelo UltraMsg para telefone final %s", to[-4:])


async def _claim_message(session: AsyncSession, message_id: str) -> bool:
    statement = (
        insert(ProcessedWebhookMessageModel)
        .values(provider=PROVIDER, message_id=message_id)
        .on_conflict_do_nothing(index_elements=["provider", "message_id"])
    )
    result = await session.execute(statement)
    await session.commit()
    return result.rowcount == 1


async def _release_message(session: AsyncSession, message_id: str) -> None:
    await session.execute(
        delete(ProcessedWebhookMessageModel).where(
            ProcessedWebhookMessageModel.provider == PROVIDER,
            ProcessedWebhookMessageModel.message_id == message_id,
        )
    )
    await session.commit()


@router.post("/{webhook_secret}")
async def receive_ultramsg_webhook(
    webhook_secret: str,
    payload: dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    clientes: ClienteRepository = Depends(cliente_repository),
    procedimentos: ProcedimentoRepository = Depends(procedimento_repository),
    agendamentos: AgendamentoRepository = Depends(agendamento_repository),
    tempos_trabalho: TempoTrabalhoRepository = Depends(tempo_trabalho_repository),
):
    configured_secret = _webhook_secret()
    if not configured_secret or webhook_secret != configured_secret:
        raise HTTPException(status_code=404, detail="Webhook não encontrado")

    message = _extract_message(payload)
    if message is None:
        return {
            "ok": True,
            "ignored": True,
            "event_type": payload.get("event_type"),
        }

    telefone, texto = message
    message_id = str((payload.get("data") or {}).get("id", "")).strip()
    if not message_id:
        logger.info("Webhook UltraMsg ignorado: message_id ausente")
        return {"ok": False, "ignored": True, "reason": "message_id ausente"}
    if not await _claim_message(session, message_id):
        logger.info("Mensagem UltraMsg duplicada ignorada: %s", message_id)
        return {"ok": True, "duplicate": True}

    logger.info("Mensagem UltraMsg recebida do telefone final %s", telefone[-4:])
    try:
        contexto = AtendimentoService(clientes, procedimentos, agendamentos, tempos_trabalho)
        resposta = await run_agent(texto, telefone, contexto)
        await _send_message(telefone, resposta)
    except Exception:
        await _release_message(session, message_id)
        raise
    return {"ok": True}
