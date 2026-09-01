import os
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field

from app.agent.graph import run_agent
from app.api.routes.dependencies import (
    agendamento_repository,
    cliente_repository,
    procedimento_repository,
    tempo_trabalho_repository,
)
from app.application.services.atendimento_service import AtendimentoService
from app.infrastructure.repositories.repositorie_agendamento import AgendamentoRepository
from app.infrastructure.repositories.repositorie_cliente import ClienteRepository
from app.infrastructure.repositories.repositorie_procedimento import ProcedimentoRepository
from app.infrastructure.repositories.repositorie_tempo_trabalho import TempoTrabalhoRepository

router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp"])
logger = logging.getLogger(__name__)


class WhatsAppWebhookPayload(BaseModel):
    """Payload recebido da Cloud API do WhatsApp."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "object": "whatsapp_business_account",
                "entry": [
                    {
                        "changes": [
                            {
                                "value": {
                                    "messages": [
                                        {
                                            "from": "5521980494500",
                                            "type": "text",
                                            "text": {"body": "Olá"},
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ],
            }
        }
    )
    object: str | None = None
    entry: list[dict[str, Any]] = Field(default_factory=list)


def _setting(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@router.get("")
async def verify_webhook(
    mode: str | None = Query(None, alias="hub.mode"),
    token: str | None = Query(None, alias="hub.verify_token"),
    challenge: str | None = Query(None, alias="hub.challenge"),
):
    """Endpoint usado pela Meta para validar a URL do webhook."""
    expected_token = _setting("WHATSAPP_VERIFY_TOKEN") or _setting("BUSINESS_ID")
    if mode == "subscribe" and token and challenge and token == expected_token:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Webhook verification failed")


async def _send_message(to: str, text: str) -> None:
    phone_number_id = _setting("PHONE_NUMBER_ID")
    access_token = _setting("ZAP_TOKEN")
    if not phone_number_id or not access_token:
        raise RuntimeError("PHONE_NUMBER_ID e ZAP_TOKEN precisam estar configurados")

    version = _setting("WHATSAPP_API_VERSION", "v20.0")
    url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)
    response.raise_for_status()


def _text_messages(payload: dict[str, Any]) -> list[tuple[str, str]]:
    """Extrai somente mensagens de texto recebidas no formato Cloud API."""
    messages: list[tuple[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                sender = message.get("from")
                body = message.get("text", {}).get("body")
                if sender and body:
                    messages.append((sender, body))
    return messages


@router.post("")
async def receive_webhook(
    payload: WhatsAppWebhookPayload = Body(...),
    clientes: ClienteRepository = Depends(cliente_repository),
    procedimentos: ProcedimentoRepository = Depends(procedimento_repository),
    agendamentos: AgendamentoRepository = Depends(agendamento_repository),
    tempos_trabalho: TempoTrabalhoRepository = Depends(tempo_trabalho_repository),
):
    """Recebe mensagens da Meta, executa o agente e responde ao cliente."""
    if payload.object != "whatsapp_business_account":
        logger.info("Webhook WhatsApp ignorado: object=%s", payload.object)
        return {"ok": True}

    contexto = AtendimentoService(clientes, procedimentos, agendamentos, tempos_trabalho)
    mensagens = _text_messages(payload.model_dump())
    logger.info("Webhook WhatsApp recebeu %d mensagem(ns) de texto", len(mensagens))
    for telefone, mensagem in mensagens:
        logger.info("Executando agente para mensagem recebida do telefone final %s", telefone[-4:])
        resposta = await run_agent(mensagem, telefone, contexto)
        await _send_message(telefone, resposta)
        logger.info("Resposta enviada ao WhatsApp para telefone final %s", telefone[-4:])
    return {"ok": True}
