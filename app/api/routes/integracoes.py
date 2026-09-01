import ast
import hmac
import json
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user, require_admin
import httpx
from app.api.schemas.integracoes import AIIntegrationCreate, AIIntegrationUpdate, ConversationMessageCreate, ConversationStatusUpdate, WhatsAppIntegrationCreate, WhatsAppIntegrationUpdate
from app.infrastructure.database.db import get_session
from app.infrastructure.database.models.models import AIIntegrationModel, ProcessedWebhookMessageModel, UserModel, WhatsAppIntegrationModel
from app.infrastructure.database import mongo
from app.infrastructure.security.secrets import decrypt_secret, encrypt_secret
from app.agent.graph import run_agent
from app.application.services.atendimento_service import AtendimentoService
from app.api.routes.dependencies import (
    cliente_repository,
    procedimento_repository,
    agendamento_repository,
    tempo_trabalho_repository,
)
from app.infrastructure.repositories.repositorie_cliente import ClienteRepository
from app.infrastructure.repositories.repositorie_procedimento import ProcedimentoRepository
from app.infrastructure.repositories.repositorie_agendamento import AgendamentoRepository
from app.infrastructure.repositories.repositorie_tempo_trabalho import TempoTrabalhoRepository

router = APIRouter(prefix="/integracoes", tags=["Integrações"])
webhook_router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _whatsapp_view(item: WhatsAppIntegrationModel) -> dict[str, Any]:
    base_url = os.getenv("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
    secret = decrypt_secret(item.webhook_token_encriptado) if item.webhook_token_encriptado else None
    if item.tipo == "meta":
        webhook_url = f"{base_url}/webhooks/whatsapp"
    elif item.tipo == "ultramsg":
        webhook_url = f"{base_url}/webhooks/ultramsg/{secret}" if secret else f"{base_url}/webhooks/ultramsg/{{webhook_secret}}"
    elif item.tipo == "openwa":
        # O OpenWA fica na rede Docker e chama a API pelo nome do serviço.
        internal_url = os.getenv("OPENWA_WEBHOOK_URL", "http://api:8000/webhooks/openwa")
        webhook_url = f"{internal_url}/{{webhook_secret}}"
    else:
        webhook_url = f"{base_url}/webhooks/whatsapp/{item.id}/{{webhook_secret}}" if secret else f"{base_url}/webhooks/whatsapp/{item.id}"
    return {"id": item.id, "nome": item.nome, "tipo": item.tipo, "prioridade": item.prioridade, "ativo": item.ativo, "credenciais_configuradas": True, "webhook_configurado": bool(secret), "webhook_url": webhook_url, "webhook_verify_token": None}


def _ai_view(item: AIIntegrationModel) -> dict[str, Any]:
    return {"id": item.id, "nome": item.nome, "tipo": item.tipo, "modelo": item.modelo, "base_url": item.base_url, "prioridade": item.prioridade, "ativo": item.ativo, "api_key_configurada": True}


async def _claim_webhook_message(session: AsyncSession, provider: str, message_id: str) -> bool:
    statement = (
        insert(ProcessedWebhookMessageModel)
        .values(provider=provider, message_id=message_id)
        .on_conflict_do_nothing(index_elements=["provider", "message_id"])
    )
    result = await session.execute(statement)
    await session.commit()
    return result.rowcount == 1


async def _release_webhook_message(session: AsyncSession, provider: str, message_id: str) -> None:
    await session.execute(
        delete(ProcessedWebhookMessageModel).where(
            ProcessedWebhookMessageModel.provider == provider,
            ProcessedWebhookMessageModel.message_id == message_id,
        )
    )
    await session.commit()


@router.get("/whatsapp")
async def listar_whatsapp(session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    items = (await session.execute(select(WhatsAppIntegrationModel).order_by(WhatsAppIntegrationModel.prioridade, WhatsAppIntegrationModel.id))).scalars().all()
    return [_whatsapp_view(item) for item in items]


@router.post("/whatsapp", status_code=status.HTTP_201_CREATED)
async def criar_whatsapp(payload: WhatsAppIntegrationCreate, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = WhatsAppIntegrationModel(nome=payload.nome, tipo=payload.tipo, credenciais_encriptadas=encrypt_secret(json.dumps(payload.credenciais)), webhook_token_encriptado=encrypt_secret(payload.webhook_token) if payload.webhook_token else None, prioridade=payload.prioridade, ativo=payload.ativo)
    session.add(item); await session.commit(); await session.refresh(item)
    return _whatsapp_view(item)


@router.put("/whatsapp/{integration_id}")
async def atualizar_whatsapp(integration_id: int, payload: WhatsAppIntegrationUpdate, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = await session.get(WhatsAppIntegrationModel, integration_id)
    if not item: raise HTTPException(404, "Integração WhatsApp não encontrada")
    values = payload.model_dump(exclude_unset=True)
    for key in ("nome", "tipo", "prioridade", "ativo"):
        if key in values: setattr(item, key, values[key])
    if payload.credenciais is not None: item.credenciais_encriptadas = encrypt_secret(json.dumps(payload.credenciais))
    if "webhook_token" in values: item.webhook_token_encriptado = encrypt_secret(payload.webhook_token) if payload.webhook_token else None
    await session.commit(); await session.refresh(item)
    return _whatsapp_view(item)


@router.delete("/whatsapp/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_whatsapp(integration_id: int, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = await session.get(WhatsAppIntegrationModel, integration_id)
    if not item: raise HTTPException(404, "Integração WhatsApp não encontrada")
    await session.delete(item); await session.commit()


@router.get("/ia")
async def listar_ia(session: AsyncSession = Depends(get_session), _: UserModel = Depends(get_current_user)):
    items = (await session.execute(select(AIIntegrationModel).order_by(AIIntegrationModel.prioridade, AIIntegrationModel.id))).scalars().all()
    return [_ai_view(item) for item in items]


@router.post("/ia", status_code=status.HTTP_201_CREATED)
async def criar_ia(payload: AIIntegrationCreate, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = AIIntegrationModel(nome=payload.nome, tipo=payload.tipo, modelo=payload.modelo, base_url=payload.base_url, api_key_encriptada=encrypt_secret(payload.api_key), prioridade=payload.prioridade, ativo=payload.ativo)
    session.add(item); await session.commit(); await session.refresh(item)
    return _ai_view(item)


@router.put("/ia/{integration_id}")
async def atualizar_ia(integration_id: int, payload: AIIntegrationUpdate, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = await session.get(AIIntegrationModel, integration_id)
    if not item: raise HTTPException(404, "Integração de IA não encontrada")
    values = payload.model_dump(exclude_unset=True)
    for key in ("nome", "tipo", "modelo", "base_url", "prioridade", "ativo"):
        if key in values: setattr(item, key, values[key])
    if payload.api_key is not None: item.api_key_encriptada = encrypt_secret(payload.api_key)
    await session.commit(); await session.refresh(item)
    return _ai_view(item)


@router.delete("/ia/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_ia(integration_id: int, session: AsyncSession = Depends(get_session), _: UserModel = Depends(require_admin)):
    item = await session.get(AIIntegrationModel, integration_id)
    if not item: raise HTTPException(404, "Integração de IA não encontrada")
    await session.delete(item); await session.commit()


@router.get("/conversas")
async def listar_conversas(
    session: AsyncSession = Depends(get_session),
    clientes: ClienteRepository = Depends(cliente_repository),
    _: UserModel = Depends(get_current_user),
):
    conversas = await mongo.list_conversations()
    clientes_por_telefone = {
        "".join(ch for ch in (cliente.telefone or "") if ch.isdigit()): cliente.nome
        for cliente in await clientes.list_clientes()
        if cliente.telefone
    }
    for conversa in conversas:
        nome = clientes_por_telefone.get(conversa["telefone"])
        if nome:
            conversa["nome_contato"] = nome
    return conversas


@router.get("/conversas/{conversation_id}/mensagens")
async def listar_mensagens(conversation_id: str, session: AsyncSession = Depends(get_session), _: UserModel = Depends(get_current_user)):
    try:
        return await mongo.list_messages(str(conversation_id))
    except (KeyError, ValueError):
        raise HTTPException(404, "Conversa não encontrada")


async def _send_through_integration(
    integration: WhatsAppIntegrationModel,
    telefone: str,
    conteudo: str,
    chat_id: str | None = None,
) -> None:
    try:
        credentials = json.loads(decrypt_secret(integration.credenciais_encriptadas))
    except (ValueError, SyntaxError):
        credentials = ast.literal_eval(decrypt_secret(integration.credenciais_encriptadas))
    async with httpx.AsyncClient(timeout=30) as client:
        if integration.tipo == "meta":
            phone_number_id = credentials.get("phone_number_id") or credentials.get("PHONE_NUMBER_ID")
            token = credentials.get("access_token") or credentials.get("token") or credentials.get("ZAP_TOKEN")
            version = credentials.get("api_version", "v20.0")
            if not phone_number_id or not token: raise RuntimeError("Meta requer phone_number_id e access_token")
            response = await client.post(f"https://graph.facebook.com/{version}/{phone_number_id}/messages", headers={"Authorization": f"Bearer {token}"}, json={"messaging_product": "whatsapp", "to": telefone, "type": "text", "text": {"preview_url": False, "body": conteudo}})
        elif integration.tipo == "ultramsg":
            instance = credentials.get("instance_id") or credentials.get("instance")
            token = credentials.get("token")
            if not instance or not token: raise RuntimeError("UltraMsg requer instance_id e token")
            response = await client.post(f"https://api.ultramsg.com/{instance}/messages/chat", data={"token": token, "to": telefone, "body": conteudo})
        elif integration.tipo == "evolution":
            base_url = str(credentials.get("base_url", "")).rstrip("/")
            instance = credentials.get("instance") or credentials.get("instance_name")
            api_key = credentials.get("api_key") or credentials.get("token")
            if not base_url or not instance or not api_key: raise RuntimeError("Evolution requer base_url, instance e api_key")
            response = await client.post(f"{base_url}/message/sendText/{instance}", headers={"apikey": api_key}, json={"number": telefone, "text": conteudo})
        elif integration.tipo == "openwa":
            base_url = str(credentials.get("base_url") or credentials.get("url") or "").rstrip("/")
            api_key = credentials.get("api_key") or credentials.get("key") or credentials.get("token")
            session_id = credentials.get("session_id") or credentials.get("session")
            if not base_url or not api_key or not session_id:
                raise RuntimeError("OpenWA requer base_url, api_key e session_id")
            # Keep the original OpenWA JID when replying to an inbound
            # message. LID recipients (e.g. ...@lid) must not be converted to
            # ...@c.us, otherwise OpenWA cannot resolve the chat.
            chat_id = chat_id or (telefone if "@" in telefone else f"{telefone}@c.us")
            response = await client.post(
                f"{base_url}/api/sessions/{session_id}/messages/send-text",
                headers={"X-API-Key": api_key},
                # OpenWA's send-text contract accepts chatId and text.
                # Extra fields such as linkPreview are rejected by v0.23.x.
                json={"chatId": chat_id, "text": conteudo},
            )
        else:
            raise RuntimeError(f"Envio ainda não implementado para {integration.tipo}")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            # Preserve OpenWA's validation message; otherwise the webhook only
            # exposes a generic 500 and hides the actual send-text failure.
            detail = response.text[:1000]
            raise RuntimeError(
                f"Falha ao enviar mensagem pelo provedor {integration.tipo} "
                f"({response.status_code}): {detail}"
            ) from error


@router.post("/conversas/{conversation_id}/mensagens", status_code=status.HTTP_201_CREATED)
async def enviar_mensagem(conversation_id: str, payload: ConversationMessageCreate, session: AsyncSession = Depends(get_session), _: UserModel = Depends(get_current_user)):
    conversation = await mongo.get_conversation(conversation_id)
    if not conversation: raise HTTPException(404, "Conversa não encontrada")
    integration = await session.get(WhatsAppIntegrationModel, conversation["integration_id"])
    if not integration or not integration.ativo: raise HTTPException(409, "A integração desta conversa está inativa")
    try:
        await _send_through_integration(
            integration,
            conversation["telefone"],
            payload.conteudo,
            chat_id=conversation.get("chat_id"),
        )
    except Exception as exc:
        raise HTTPException(502, "Não foi possível enviar a mensagem pelo provedor") from exc
    try:
        return await mongo.append_message(conversation_id, direcao="saida", tipo="text", conteudo=payload.conteudo)
    except (KeyError, ValueError):
        raise HTTPException(404, "Conversa não encontrada")


@router.patch("/conversas/{conversation_id}")
async def atualizar_status_conversa(conversation_id: str, payload: ConversationStatusUpdate, session: AsyncSession = Depends(get_session), _: UserModel = Depends(get_current_user)):
    try:
        item = await mongo.update_status(conversation_id, payload.status)
    except ValueError:
        item = None
    if not item: raise HTTPException(404, "Conversa não encontrada")
    return {"id": str(item["_id"]), "status": item["status"]}


async def _get_webhook_integration(integration_id: int, webhook_secret: str | None, session: AsyncSession) -> WhatsAppIntegrationModel:
    integration = await session.get(WhatsAppIntegrationModel, integration_id)
    if not integration or not integration.ativo: raise HTTPException(404, "Integração não encontrada")
    configured_secret = decrypt_secret(integration.webhook_token_encriptado) if integration.webhook_token_encriptado else ""
    if configured_secret and (not webhook_secret or not hmac.compare_digest(webhook_secret, configured_secret)): raise HTTPException(404, "Webhook não encontrado")
    if webhook_secret and not configured_secret: raise HTTPException(404, "Webhook não encontrado")
    return integration


@webhook_router.get("/whatsapp/{integration_id}/{webhook_secret}")
async def verificar_webhook(integration_id: int, webhook_secret: str, mode: str | None = Query(None, alias="hub.mode"), token: str | None = Query(None, alias="hub.verify_token"), challenge: str | None = Query(None, alias="hub.challenge"), session: AsyncSession = Depends(get_session)):
    await _get_webhook_integration(integration_id, webhook_secret, session)
    if mode == "subscribe" and token == webhook_secret and challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(403, "Verificação do webhook inválida")


@webhook_router.get("/whatsapp/{integration_id}")
async def verificar_webhook_sem_segredo(integration_id: int, mode: str | None = Query(None, alias="hub.mode"), challenge: str | None = Query(None, alias="hub.challenge"), session: AsyncSession = Depends(get_session)):
    await _get_webhook_integration(integration_id, None, session)
    if mode == "subscribe" and challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(403, "Verificação do webhook inválida")


@webhook_router.post("/whatsapp/{integration_id}/{webhook_secret}")
async def receber_webhook(
    integration_id: int,
    webhook_secret: str,
    request: Request,
    payload: dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    clientes: ClienteRepository = Depends(cliente_repository),
    procedimentos: ProcedimentoRepository = Depends(procedimento_repository),
    agendamentos: AgendamentoRepository = Depends(agendamento_repository),
    tempos_trabalho: TempoTrabalhoRepository = Depends(tempo_trabalho_repository),
    openwa_signature: str | None = Header(default=None, alias="X-OpenWA-Signature"),
    openwa_idempotency_key: str | None = Header(default=None, alias="X-OpenWA-Idempotency-Key"),
):
    integration = await _get_webhook_integration(integration_id, webhook_secret, session)
    if integration.tipo == "openwa":
        configured = decrypt_secret(integration.webhook_token_encriptado) if integration.webhook_token_encriptado else ""
        raw_body = await request.body() if request else b""
        expected = "sha256=" + hmac.new(configured.encode(), raw_body, digestmod="sha256").hexdigest()
        if not configured or not openwa_signature or not hmac.compare_digest(openwa_signature, expected):
            raise HTTPException(401, "Assinatura do webhook OpenWA inválida")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    # OpenWA v5 envelopes use payload.message; v4 webhooks normally send the
    # Message object directly. Supporting both keeps the adapter tolerant.
    if integration.tipo == "openwa" and isinstance(payload.get("payload"), dict):
        data = payload["payload"].get("message") if isinstance(payload["payload"].get("message"), dict) else payload["payload"]
    evolution_key = data.get("key") if isinstance(data.get("key"), dict) else {}
    evolution_message = data.get("message") if isinstance(data.get("message"), dict) else {}
    is_evolution = payload.get("event") == "messages.upsert" or bool(evolution_key)
    is_openwa = integration.tipo == "openwa"
    openwa_chat_id = None
    if is_openwa:
        openwa_candidates = [
            data.get("remoteJidAlt"),
            data.get("remoteJid"),
            data.get("from"),
            data.get("sender"),
        ]
        openwa_chat_id = next(
            (str(value).strip() for value in openwa_candidates if isinstance(value, str) and "@" in value),
            None,
        )
    if (is_evolution and evolution_key.get("fromMe")) or (is_openwa and data.get("fromMe")):
        return {"ok": True, "ignored": True, "reason": "from_me"}

    telefone = str(
        evolution_key.get("remoteJid")
        or evolution_key.get("remoteJidAlt")
        or data.get("from")
        or data.get("phone")
        or data.get("sender")
        or data.get("from")
        or ""
    ).split("@", 1)[0].split(":", 1)[0]
    texto = str(
        evolution_message.get("conversation")
        or (evolution_message.get("extendedTextMessage") or {}).get("text")
        or (evolution_message.get("imageMessage") or {}).get("caption")
        or data.get("body")
        or data.get("text")
        or ""
    ).strip()
    external_id = str(
        evolution_key.get("id")
        or openwa_idempotency_key
        or payload.get("idempotencyKey")
        or data.get("id")
        or ""
    ).strip() or None
    nome_contato = data.get("pushName") or data.get("name")
    if payload.get("object") == "whatsapp_business_account":
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                for message in (change.get("value") or {}).get("messages", []):
                    if message.get("type") == "text":
                        telefone = str(message.get("from", "")); texto = str((message.get("text") or {}).get("body", "")).strip()
                        external_id = str(message.get("id") or "").strip() or external_id
                        break
    if not telefone or not texto: return {"ok": True, "ignored": True}
    provider = f"{integration.tipo}:{integration_id}"
    if (is_evolution or is_openwa) and external_id and not await _claim_webhook_message(session, provider, external_id):
        return {"ok": True, "duplicate": True}
    cliente = await clientes.get_cliente_by_telefone(telefone)
    if cliente:
        nome_contato = cliente.nome
    conversation = await mongo.get_by_identity(integration_id, telefone)
    if not conversation:
        conversation = await mongo.create_conversation(integration_id, telefone, nome_contato, openwa_chat_id)
    elif is_openwa:
        await mongo.update_contact(
            str(conversation["_id"]),
            nome_contato=nome_contato,
            chat_id=openwa_chat_id,
        )
    try:
        await mongo.append_message(str(conversation["_id"]), external_id=external_id, direcao="entrada", tipo="text", conteudo=texto)
    except (KeyError, ValueError):
        raise HTTPException(404, "Conversa não encontrada")

    if integration and integration.tipo in ("evolution", "openwa"):
        try:
            contexto = AtendimentoService(clientes, procedimentos, agendamentos, tempos_trabalho)
            resposta = await run_agent(texto, telefone, contexto)
            await _send_through_integration(integration, telefone, resposta, chat_id=openwa_chat_id)
            await mongo.append_message(str(conversation["_id"]), direcao="saida", tipo="text", conteudo=resposta)
        except Exception:
            if external_id:
                await _release_webhook_message(session, provider, external_id)
            raise
    return {"ok": True, "conversation_id": str(conversation["_id"])}


@webhook_router.post("/whatsapp/{integration_id}")
async def receber_webhook_sem_segredo(
    integration_id: int,
    request: Request,
    payload: dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    clientes: ClienteRepository = Depends(cliente_repository),
    procedimentos: ProcedimentoRepository = Depends(procedimento_repository),
    agendamentos: AgendamentoRepository = Depends(agendamento_repository),
    tempos_trabalho: TempoTrabalhoRepository = Depends(tempo_trabalho_repository),
    openwa_signature: str | None = Header(default=None, alias="X-OpenWA-Signature"),
):
    await _get_webhook_integration(integration_id, None, session)
    return await receber_webhook(
        integration_id, "", request, payload, session,
        clientes, procedimentos, agendamentos, tempos_trabalho,
        openwa_signature=openwa_signature,
    )


async def _primary_integration(tipo: str, session: AsyncSession) -> WhatsAppIntegrationModel | None:
    return (await session.execute(select(WhatsAppIntegrationModel).where(WhatsAppIntegrationModel.tipo == tipo, WhatsAppIntegrationModel.ativo.is_(True)).order_by(WhatsAppIntegrationModel.prioridade, WhatsAppIntegrationModel.id))).scalars().first()


@webhook_router.get("/whatsapp")
async def verificar_meta_webhook(mode: str | None = Query(None, alias="hub.mode"), token: str | None = Query(None, alias="hub.verify_token"), challenge: str | None = Query(None, alias="hub.challenge"), session: AsyncSession = Depends(get_session)):
    integration = await _primary_integration("meta", session)
    if not integration: raise HTTPException(404, "Nenhuma integração Meta ativa")
    secret = decrypt_secret(integration.webhook_token_encriptado) if integration.webhook_token_encriptado else ""
    if mode == "subscribe" and challenge and (not secret or token == secret):
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(403, "Verificação do webhook inválida")


@webhook_router.post("/whatsapp")
async def receber_meta_webhook(
    request: Request,
    payload: dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    clientes: ClienteRepository = Depends(cliente_repository),
    procedimentos: ProcedimentoRepository = Depends(procedimento_repository),
    agendamentos: AgendamentoRepository = Depends(agendamento_repository),
    tempos_trabalho: TempoTrabalhoRepository = Depends(tempo_trabalho_repository),
):
    integration = await _primary_integration("meta", session)
    if not integration: raise HTTPException(404, "Nenhuma integração Meta ativa")
    secret = decrypt_secret(integration.webhook_token_encriptado) if integration.webhook_token_encriptado else ""
    return await receber_webhook(
        integration.id, secret, request, payload, session,
        clientes, procedimentos, agendamentos, tempos_trabalho,
    )


@webhook_router.post("/ultramsg/{webhook_secret}")
async def receber_ultramsg_webhook(
    webhook_secret: str,
    request: Request,
    payload: dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
):
    integrations = (await session.execute(select(WhatsAppIntegrationModel).where(WhatsAppIntegrationModel.tipo == "ultramsg", WhatsAppIntegrationModel.ativo.is_(True)).order_by(WhatsAppIntegrationModel.prioridade, WhatsAppIntegrationModel.id))).scalars().all()
    for integration in integrations:
        if integration.webhook_token_encriptado and hmac.compare_digest(webhook_secret, decrypt_secret(integration.webhook_token_encriptado)):
            return await receber_webhook(integration.id, webhook_secret, request, payload, session)
    raise HTTPException(404, "Webhook UltraMsg não encontrado")


@webhook_router.post("/openwa/{webhook_secret}")
async def receber_openwa_webhook(
    webhook_secret: str,
    request: Request,
    payload: dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session),
    clientes: ClienteRepository = Depends(cliente_repository),
    procedimentos: ProcedimentoRepository = Depends(procedimento_repository),
    agendamentos: AgendamentoRepository = Depends(agendamento_repository),
    tempos_trabalho: TempoTrabalhoRepository = Depends(tempo_trabalho_repository),
    openwa_signature: str | None = Header(default=None, alias="X-OpenWA-Signature"),
    openwa_idempotency_key: str | None = Header(default=None, alias="X-OpenWA-Idempotency-Key"),
):
    integrations = (await session.execute(select(WhatsAppIntegrationModel).where(
        WhatsAppIntegrationModel.tipo == "openwa",
        WhatsAppIntegrationModel.ativo.is_(True),
    ).order_by(WhatsAppIntegrationModel.prioridade, WhatsAppIntegrationModel.id))).scalars().all()
    for integration in integrations:
        configured = decrypt_secret(integration.webhook_token_encriptado) if integration.webhook_token_encriptado else ""
        if configured and hmac.compare_digest(webhook_secret, configured):
            return await receber_webhook(
                integration.id, webhook_secret, request, payload, session,
                clientes, procedimentos, agendamentos, tempos_trabalho,
                openwa_signature, openwa_idempotency_key,
            )
    raise HTTPException(404, "Webhook OpenWA não encontrado")
