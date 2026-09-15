import ast
import asyncio
import base64
import binascii
import html
import hmac
import json
import logging
import os
from datetime import datetime
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Body, Cookie, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user, require_admin
import httpx
from app.api.schemas.integracoes import AIIntegrationCreate, AIIntegrationUpdate, ConversationAttachmentCreate, ConversationMessageCreate, ConversationStatusUpdate, WhatsAppIntegrationCreate, WhatsAppIntegrationUpdate
from app.infrastructure.database.db import AsyncSessionLocal, get_session
from app.infrastructure.database.models.models import AIIntegrationModel, ProcessedWebhookMessageModel, UserModel, WhatsAppIntegrationModel
from app.infrastructure.database import mongo
from app.infrastructure.events.conversation_events import conversation_events
from app.infrastructure.security.auth import decode_token
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
logger = logging.getLogger(__name__)


async def _authenticated_event_user(lia_session: str | None) -> int:
    """Valida o cookie sem manter uma sessão SQL aberta durante todo o stream."""
    if not lia_session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Autenticação necessária")
    try:
        user_id = int(decode_token(lia_session)["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado")
    async with AsyncSessionLocal() as session:
        user = await session.get(UserModel, user_id)
        if not user or not user.ativo:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário inativo")
    return user_id


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
    page: int | None = Query(default=None, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    clientes: ClienteRepository = Depends(cliente_repository),
    _: UserModel = Depends(get_current_user),
):
    if page is None:
        conversas = await mongo.list_conversations()
        total = len(conversas)
    else:
        conversas, total = await mongo.list_conversations_page(page, page_size)
        total_pages = max(1, (total + page_size - 1) // page_size)
        if page > total_pages:
            page = total_pages
            conversas, total = await mongo.list_conversations_page(page, page_size)
    clientes_por_telefone = {
        "".join(ch for ch in (cliente.telefone or "") if ch.isdigit()): cliente.nome
        for cliente in await clientes.list_clientes()
        if cliente.telefone
    }
    for conversa in conversas:
        nome = clientes_por_telefone.get(conversa["telefone"])
        if nome:
            conversa["nome_contato"] = nome
        if not conversa.get("foto_perfil"):
            integration = await session.get(WhatsAppIntegrationModel, conversa.get("integration_id"))
            if integration and integration.tipo == "openwa":
                chat_id = conversa.get("chat_id") or f'{conversa["telefone"]}@c.us'
                _, foto = await _openwa_contact_details(integration, chat_id)
                if foto:
                    conversa["foto_perfil"] = foto
                    await mongo.update_contact(str(conversa["id"]), foto_perfil=foto)
        if conversa.get("foto_perfil"):
            conversa["foto_perfil"] = f"/api/integracoes/conversas/{conversa['id']}/foto"
    if page is None:
        return conversas
    return {
        "items": conversas,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.post("/conversas/sincronizar-openwa")
async def sincronizar_historico_openwa(
    session: AsyncSession = Depends(get_session),
    _: UserModel = Depends(require_admin),
):
    """Recupera do OpenWA as mensagens ainda ausentes na inbox local."""
    integrations = {
        item.id: item
        for item in (
            await session.execute(
                select(WhatsAppIntegrationModel).where(
                    WhatsAppIntegrationModel.tipo == "openwa",
                    WhatsAppIntegrationModel.ativo.is_(True),
                )
            )
        ).scalars().all()
    }
    conversations = [
        item for item in await mongo.list_conversations()
        if item.get("integration_id") in integrations
    ]
    imported = 0
    examined = 0
    already_synchronized = 0
    failures: list[dict[str, str]] = []
    for conversation in conversations:
        if not await mongo.claim_history_sync(conversation["id"]):
            already_synchronized += 1
            continue
        try:
            added, found = await _sync_openwa_conversation(
                integrations[conversation["integration_id"]],
                conversation,
            )
            await mongo.complete_history_sync(conversation["id"])
            imported += added
            examined += found
        except Exception as exc:
            await mongo.release_history_sync(conversation["id"])
            logger.exception("Falha ao sincronizar a conversa OpenWA %s", conversation["id"])
            failures.append({"conversation_id": conversation["id"], "erro": str(exc)[:300]})
    return {
        "conversas": len(conversations),
        "mensagens_examinadas": examined,
        "mensagens_importadas": imported,
        "conversas_ja_sincronizadas": already_synchronized,
        "falhas": failures,
    }


@router.get("/conversas/nao-lidas")
async def resumo_nao_lidas(_: UserModel = Depends(get_current_user)):
    return await mongo.unread_summary()


@router.get("/conversas/eventos")
async def eventos_conversas(lia_session: str | None = Cookie(default=None)):
    await _authenticated_event_user(lia_session)

    async def stream():
        yield "retry: 3000\n\n"
        async for queue in conversation_events.subscribe():
            while True:
                try:
                    conversation_id = await asyncio.wait_for(queue.get(), timeout=20)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                    continue
                payload = json.dumps({"conversation_id": conversation_id})
                yield f"event: conversations.changed\ndata: {payload}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversas/{conversation_id}/foto")
async def foto_conversa(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
    _: UserModel = Depends(get_current_user),
):
    try:
        conversa = await mongo.get_conversation(conversation_id)
    except (KeyError, ValueError):
        raise HTTPException(404, "Conversa não encontrada")
    if not conversa:
        raise HTTPException(404, "Conversa não encontrada")

    foto = conversa.get("foto_perfil")
    integration = await session.get(WhatsAppIntegrationModel, conversa.get("integration_id"))
    if integration and integration.tipo == "openwa":
        chat_id = conversa.get("chat_id") or f'{conversa["telefone"]}@c.us'
        _, refreshed_photo = await _openwa_contact_details(integration, chat_id)
        if refreshed_photo:
            foto = refreshed_photo
            await mongo.update_contact(conversation_id, foto_perfil=foto)
    if not isinstance(foto, str) or not foto.startswith(("http://", "https://")):
        raise HTTPException(404, "Foto não encontrada")

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        response = await client.get(foto, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://web.whatsapp.com/"})
    if not response.is_success or not response.content:
        raise HTTPException(404, "Foto não disponível")
    media_type = response.headers.get("content-type", "image/jpeg").split(";", 1)[0]
    return Response(content=response.content, media_type=media_type)


@router.get("/conversas/{conversation_id}/mensagens")
async def listar_mensagens(conversation_id: str, _: UserModel = Depends(get_current_user)):
    try:
        # O webhook persiste mensagens novas antes de publicar o evento SSE.
        # Consultar todo o histórico do OpenWA aqui atrasava cada atualização
        # em tempo real; a recuperação retroativa permanece na rota dedicada.
        messages = await mongo.list_messages(str(conversation_id))
        await mongo.mark_read(conversation_id)
        return messages
    except (KeyError, ValueError):
        raise HTTPException(404, "Conversa não encontrada")


async def _send_through_integration(
    integration: WhatsAppIntegrationModel,
    telefone: str,
    conteudo: str,
    chat_id: str | None = None,
) -> str | None:
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
        return _provider_message_id(response)


def _provider_message_id(response: httpx.Response) -> str | None:
    """Extrai o ID da mensagem retornado pelo provedor, quando disponível."""
    try:
        data: Any = response.json()
    except ValueError:
        return None

    def find_id(value: Any) -> str | None:
        if not isinstance(value, dict):
            return None
        for field in ("messageId", "message_id", "id"):
            candidate = value.get(field)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        key = value.get("key")
        if isinstance(key, dict):
            candidate = key.get("id")
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        for field in ("result", "message", "data"):
            candidate = find_id(value.get(field))
            if candidate:
                return candidate
        return None

    return find_id(data)


def _is_openwa_outgoing(payload: dict[str, Any], data: dict[str, Any]) -> bool:
    event = str(payload.get("event") or "").casefold()
    return bool(data.get("fromMe") or event == "message.sent")


def _openwa_phone_candidates(data: dict[str, Any], outgoing: bool) -> list[Any]:
    if outgoing:
        return [
            data.get("remoteJidAlt"),
            data.get("chatId"),
            data.get("to"),
            data.get("recipient"),
            data.get("remoteJid"),
        ]
    return [
        data.get("remoteJidAlt"),
        data.get("phone"),
        data.get("from"),
        data.get("sender"),
        data.get("chatId"),
        data.get("remoteJid"),
    ]


def _openwa_media_metadata(item: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Extrai metadados de mídia dos formatos de mensagem usados pelo OpenWA."""
    nested = item.get("message") if isinstance(item.get("message"), dict) else {}
    message_type = str(item.get("type") or item.get("messageType") or "").casefold()
    typed_message = next(
        (
            value for key, value in nested.items()
            if key.casefold().endswith("message") and isinstance(value, dict)
        ),
        {},
    )
    mime_type = next(
        (
            str(value).split(";", 1)[0].casefold()
            for value in (
                item.get("mimetype"), item.get("mimeType"),
                nested.get("mimetype"), nested.get("mimeType"),
                typed_message.get("mimetype"), typed_message.get("mimeType"),
            )
            if isinstance(value, str) and "/" in value
        ),
        None,
    )
    media_defaults = {
        "image": "image/jpeg",
        "sticker": "image/webp",
        "video": "video/mp4",
        "audio": "audio/ogg",
        "ptt": "audio/ogg",
        "document": "application/octet-stream",
    }
    media_kind = next((kind for kind in media_defaults if kind in message_type), None)
    if not mime_type and media_kind:
        mime_type = media_defaults[media_kind]
    filename = next(
        (
            str(value).strip()
            for value in (
                item.get("filename"), item.get("fileName"),
                nested.get("filename"), nested.get("fileName"),
                typed_message.get("filename"), typed_message.get("fileName"),
            )
            if isinstance(value, str) and value.strip()
        ),
        None,
    )
    return mime_type, filename, media_kind


async def _send_openwa_attachment(
    integration: WhatsAppIntegrationModel,
    chat_id: str,
    attachment: ConversationAttachmentCreate,
) -> str | None:
    try:
        credentials = json.loads(decrypt_secret(integration.credenciais_encriptadas))
    except (ValueError, SyntaxError):
        credentials = ast.literal_eval(decrypt_secret(integration.credenciais_encriptadas))
    base_url = str(credentials.get("base_url") or credentials.get("url") or "").rstrip("/")
    api_key = credentials.get("api_key") or credentials.get("key") or credentials.get("token")
    session_id = credentials.get("session_id") or credentials.get("session")
    if not base_url or not api_key or not session_id:
        raise RuntimeError("Credenciais do OpenWA incompletas")

    mime_type = attachment.mime_type.casefold()
    kind = "image" if mime_type.startswith("image/") else "video" if mime_type.startswith("video/") else "audio" if mime_type.startswith("audio/") else "document"
    payload: dict[str, Any] = {
        "chatId": chat_id,
        "base64": attachment.base64,
        "mimetype": attachment.mime_type,
    }
    if kind == "document":
        payload["filename"] = attachment.nome
    if attachment.legenda and kind in ("image", "video", "document"):
        payload["caption"] = attachment.legenda
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{base_url}/api/sessions/{session_id}/messages/send-{kind}",
            headers={"X-API-Key": api_key},
            json=payload,
        )
    response.raise_for_status()
    return _provider_message_id(response)


def _openwa_history_message(item: dict[str, Any]) -> dict[str, Any] | None:
    """Normaliza uma linha do histórico persistido do OpenWA."""
    nested_message = item.get("message") if isinstance(item.get("message"), dict) else {}
    nested_key = item.get("key") if isinstance(item.get("key"), dict) else {}
    mime_type, filename, media_kind = _openwa_media_metadata(item)
    content = str(
        item.get("body")
        or item.get("text")
        or item.get("caption")
        or item.get("content")
        or nested_message.get("conversation")
        or filename
        or ({"image": "Imagem", "sticker": "Figurinha", "video": "Vídeo", "audio": "Áudio", "ptt": "Áudio", "document": "Documento"}.get(media_kind))
        or ""
    ).strip()
    if not content:
        return None
    external_id = str(item.get("id") or item.get("messageId") or nested_key.get("id") or "").strip() or None
    raw_timestamp = item.get("timestamp") or item.get("messageTimestamp") or item.get("createdAt") or item.get("created_at")
    try:
        if isinstance(raw_timestamp, (int, float)) or (isinstance(raw_timestamp, str) and raw_timestamp.isdigit()):
            numeric = float(raw_timestamp)
            sent_at = datetime.fromtimestamp(numeric / 1000 if numeric > 10_000_000_000 else numeric)
        elif isinstance(raw_timestamp, str):
            sent_at = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
        else:
            sent_at = datetime.now()
    except (OverflowError, ValueError):
        sent_at = datetime.now()
    from_me = item.get("fromMe")
    if from_me is None:
        from_me = nested_key.get("fromMe")
    return {
        "external_id": external_id,
        "direcao": "saida" if from_me else "entrada",
        "tipo": "arquivo" if mime_type else str(item.get("type") or "text"),
        "conteudo": content,
        "enviado_em": sent_at,
        "arquivo_nome": filename,
        "mime_type": mime_type,
    }


async def _sync_openwa_conversation(integration: WhatsAppIntegrationModel, conversation: dict[str, Any]) -> tuple[int, int]:
    try:
        credentials = json.loads(decrypt_secret(integration.credenciais_encriptadas))
    except (ValueError, SyntaxError):
        credentials = ast.literal_eval(decrypt_secret(integration.credenciais_encriptadas))
    base_url = str(credentials.get("base_url") or credentials.get("url") or "").rstrip("/")
    api_key = credentials.get("api_key") or credentials.get("key") or credentials.get("token")
    session_id = credentials.get("session_id") or credentials.get("session")
    chat_id = conversation.get("chat_id") or f'{conversation["telefone"]}@c.us'
    if not base_url or not api_key or not session_id:
        raise RuntimeError("Credenciais do OpenWA incompletas")

    page_size = 100
    maximum = min(int(os.getenv("OPENWA_SYNC_MAX_MESSAGES", str(mongo.MONGODB_MAX_MESSAGES))), mongo.MONGODB_MAX_MESSAGES)
    offset = 0
    history: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        while offset < maximum:
            limit = min(page_size, maximum - offset)
            response = await client.get(
                f"{base_url}/api/sessions/{session_id}/messages",
                headers={"X-API-Key": api_key},
                params={"chatId": chat_id, "limit": limit, "offset": offset, "inlineMedia": "false"},
            )
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("messages", []) if isinstance(payload, dict) else payload
            if not isinstance(rows, list):
                raise RuntimeError("Resposta de histórico inválida do OpenWA")
            history.extend(item for item in rows if isinstance(item, dict))
            offset += len(rows)
            total = payload.get("total") if isinstance(payload, dict) else None
            if len(rows) < limit or (isinstance(total, int) and offset >= total):
                break
    normalized = [message for item in history if (message := _openwa_history_message(item))]
    imported = await mongo.import_messages(conversation["id"], normalized)
    return imported, len(history)


async def _openwa_contact_details(
    integration: WhatsAppIntegrationModel,
    contact_id: str,
) -> tuple[str | None, str | None]:
    """Busca nome e foto do contato no OpenWA sem interromper o webhook."""
    try:
        credentials = json.loads(decrypt_secret(integration.credenciais_encriptadas))
    except (ValueError, SyntaxError):
        credentials = ast.literal_eval(decrypt_secret(integration.credenciais_encriptadas))
    base_url = str(credentials.get("base_url") or credentials.get("url") or "").rstrip("/")
    api_key = credentials.get("api_key") or credentials.get("key") or credentials.get("token")
    session_id = credentials.get("session_id") or credentials.get("session")
    if not base_url or not api_key or not session_id or not contact_id:
        return None, None

    contact_path = quote(contact_id, safe="")
    headers = {"X-API-Key": api_key}
    name = None
    photo_url = None
    def extract_photo(value: Any) -> str | None:
        if isinstance(value, str):
            value = html.unescape(value).strip().strip('"\'')
            if value.startswith(("http://", "https://", "data:image/")):
                return value
            return None
        if isinstance(value, dict):
            for field in ("profilePicUrl", "profile_pic_url", "profilePictureUrl", "profilePictureURL", "profile_pic_URL", "profilePic", "profile_pic", "photo", "eurl", "imgUrl", "url"):
                photo = extract_photo(value.get(field))
                if photo:
                    return photo
            for nested in value.values():
                photo = extract_photo(nested)
                if photo:
                    return photo
        return None

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                f"{base_url}/api/sessions/{session_id}/contacts/{contact_path}",
                headers=headers,
            )
            if response.is_success:
                data = response.json()
                if isinstance(data, dict):
                    name = next(
                        (
                            str(data.get(field)).strip()
                            for field in ("name", "pushname", "pushName", "displayName", "formattedName")
                            if data.get(field)
                        ),
                        None,
                    )
                    photo_url = extract_photo(data)
        except Exception:
            logger.warning("Não foi possível consultar os dados do contato OpenWA %s", contact_id)

        if not photo_url:
            for photo_endpoint in ("profile-picture", "profile-pic"):
                try:
                    response = await client.get(
                        f"{base_url}/api/sessions/{session_id}/contacts/{contact_path}/{photo_endpoint}",
                        headers=headers,
                    )
                    if response.status_code == 404:
                        continue
                    break
                except Exception:
                    response = None
                    logger.warning("Não foi possível consultar a foto do contato OpenWA %s", contact_id)
            try:
                if response is None:
                    return name, None
                if response.is_success and response.headers.get("content-type", "").startswith("image/") and response.content:
                    media_type = response.headers["content-type"].split(";", 1)[0]
                    photo_url = f"data:{media_type};base64,{base64.b64encode(response.content).decode()}"
                elif response.is_success:
                    photo_url = extract_photo(response.json())
            except Exception:
                logger.warning("Não foi possível consultar a foto do contato OpenWA %s", contact_id)
        if not photo_url and contact_id.endswith("@lid"):
            try:
                response = await client.get(
                    f"{base_url}/api/sessions/{session_id}/contacts/{contact_path}/phone",
                    headers=headers,
                )
                if response.is_success:
                    phone_data = response.json()
                    phone = phone_data.get("phone") if isinstance(phone_data, dict) else phone_data
                    if isinstance(phone, str) and phone.strip():
                        resolved_name, resolved_photo = await _openwa_contact_details(
                            integration,
                            f"{phone.strip()}@c.us",
                        )
                        name = name or resolved_name
                        photo_url = resolved_photo
            except Exception:
                logger.warning("Não foi possível resolver o identificador @lid do contato OpenWA %s", contact_id)
        if photo_url and photo_url.startswith(base_url):
            try:
                response = await client.get(photo_url, headers=headers)
                if response.is_success and response.content:
                    media_type = response.headers.get("content-type", "image/jpeg").split(";", 1)[0]
                    if media_type.startswith("image/"):
                        photo_url = f"data:{media_type};base64,{base64.b64encode(response.content).decode()}"
            except Exception:
                logger.warning("Não foi possível materializar a foto do contato OpenWA %s", contact_id)
    return name, photo_url


def _digits(value: str | None) -> str:
    return "".join(character for character in (value or "") if character.isdigit())


def _requests_human(text: str) -> bool:
    normalized = " ".join(text.casefold().split())
    requests = (
        "atendimento humano", "atendente humano", "falar com uma pessoa",
        "falar com alguém", "falar com alguem", "quero um humano",
        "quero falar com", "pessoa real", "atendente", "humano",
    )
    return any(request in normalized for request in requests)

def _requests_course(text:str) -> bool:
    normalized = " ".join(text.casefold().split())
    requests= (
        "informações de curso", "data sobre curso", "curso", 
        "falar sobre curso","quero entrar no seu curso", 
        "matriucla de curso", "quero ser aluna do curso",
        "você ministra curso",

    )
    return any(request in normalized for request in requests )

async def notify_appointment_confirmed(
    session: AsyncSession,
    cliente: Any,
    procedimento: Any,
    data_hora: datetime,
) -> bool:
    """Envia e registra a confirmação na conversa WhatsApp do cliente."""
    telefone = _digits(getattr(cliente, "telefone", None))
    if not telefone:
        logger.warning("Agendamento confirmado sem telefone para o cliente %s", getattr(cliente, "id", "desconhecido"))
        return False

    conversations = await mongo.list_conversations()
    conversation = next(
        (item for item in conversations if _digits(item.get("telefone")) == telefone),
        None,
    )
    integration = await session.get(
        WhatsAppIntegrationModel,
        conversation["integration_id"],
    ) if conversation else None

    if not integration or not integration.ativo:
        integration = (
            await session.execute(
                select(WhatsAppIntegrationModel)
                .where(WhatsAppIntegrationModel.ativo.is_(True))
                .order_by(WhatsAppIntegrationModel.prioridade, WhatsAppIntegrationModel.id)
            )
        ).scalars().first()
    if not integration:
        logger.warning("Nenhuma integração WhatsApp ativa para notificar o cliente %s", telefone)
        return False

    if not conversation:
        conversation = await mongo.create_conversation(
            integration.id,
            telefone,
            getattr(cliente, "nome", None),
        )

    nome = getattr(cliente, "nome", None) or "cliente"
    nome_procedimento = getattr(procedimento, "nome", "procedimento")
    mensagem = (
        f"Olá, {nome}! Seu agendamento de {nome_procedimento} para "
        f"{data_hora.strftime('%d/%m/%Y às %H:%M')} foi confirmado. "
        "Esperamos por você!"
    )
    external_id = await _send_through_integration(
        integration,
        telefone,
        mensagem,
        chat_id=conversation.get("chat_id"),
    )
    await mongo.append_message(
        str(conversation["_id"] if "_id" in conversation else conversation["id"]),
        direcao="saida",
        tipo="text",
        conteudo=mensagem,
        external_id=external_id,
    )
    return True


@router.post("/conversas/{conversation_id}/mensagens", status_code=status.HTTP_201_CREATED)
async def enviar_mensagem(conversation_id: str, payload: ConversationMessageCreate, session: AsyncSession = Depends(get_session), _: UserModel = Depends(get_current_user)):
    conversation = await mongo.get_conversation(conversation_id)
    if not conversation: raise HTTPException(404, "Conversa não encontrada")
    integration = await session.get(WhatsAppIntegrationModel, conversation["integration_id"])
    if not integration or not integration.ativo: raise HTTPException(409, "A integração desta conversa está inativa")
    try:
        external_id = await _send_through_integration(
            integration,
            conversation["telefone"],
            payload.conteudo,
            chat_id=conversation.get("chat_id"),
        )
    except Exception as exc:
        raise HTTPException(502, "Não foi possível enviar a mensagem pelo provedor") from exc
    try:
        return await mongo.append_message(conversation_id, direcao="saida", tipo="text", conteudo=payload.conteudo, external_id=external_id)
    except (KeyError, ValueError):
        raise HTTPException(404, "Conversa não encontrada")


@router.post("/conversas/{conversation_id}/arquivos", status_code=status.HTTP_201_CREATED)
async def enviar_arquivo(
    conversation_id: str,
    payload: ConversationAttachmentCreate,
    session: AsyncSession = Depends(get_session),
    _: UserModel = Depends(get_current_user),
):
    conversation = await mongo.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(404, "Conversa não encontrada")
    integration = await session.get(WhatsAppIntegrationModel, conversation["integration_id"])
    if not integration or not integration.ativo:
        raise HTTPException(409, "A integração desta conversa está inativa")
    if integration.tipo != "openwa":
        raise HTTPException(409, "O envio de arquivos está disponível para conversas OpenWA")
    allowed_types = {
        "image/jpeg", "image/png", "image/webp", "image/gif",
        "video/mp4", "video/webm", "video/quicktime",
        "audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav", "audio/webm",
        "application/pdf", "text/plain", "text/csv", "application/zip",
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    mime_type = payload.mime_type.casefold().split(";", 1)[0]
    if mime_type not in allowed_types:
        raise HTTPException(415, "Tipo de arquivo não permitido")
    try:
        decoded = base64.b64decode(payload.base64, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(400, "Arquivo em base64 inválido")
    maximum = int(os.getenv("WHATSAPP_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    if not decoded or len(decoded) > maximum:
        raise HTTPException(413, f"O arquivo deve ter no máximo {maximum // (1024 * 1024)} MB")
    filename = payload.nome.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not filename or any(ord(character) < 32 for character in filename):
        raise HTTPException(400, "Nome de arquivo inválido")
    safe_payload = payload.model_copy(update={"nome": filename, "mime_type": mime_type})
    chat_id = conversation.get("chat_id") or f'{conversation["telefone"]}@c.us'
    try:
        external_id = await _send_openwa_attachment(integration, chat_id, safe_payload)
    except httpx.HTTPError as exc:
        logger.exception("Falha ao enviar arquivo pelo OpenWA")
        raise HTTPException(502, "Não foi possível enviar o arquivo pelo OpenWA") from exc
    return await mongo.append_message(
        conversation_id,
        direcao="saida",
        tipo="arquivo",
        conteudo=payload.legenda or filename,
        external_id=external_id,
        arquivo_nome=filename,
        mime_type=mime_type,
    )


@router.get("/conversas/{conversation_id}/mensagens/{message_id}/arquivo")
async def obter_arquivo(
    conversation_id: str,
    message_id: str,
    session: AsyncSession = Depends(get_session),
    _: UserModel = Depends(get_current_user),
):
    conversation = await mongo.get_conversation(conversation_id)
    message = await mongo.get_message(conversation_id, message_id)
    if not conversation or not message or not message.get("external_id") or not message.get("mime_type"):
        raise HTTPException(404, "Arquivo não encontrado")
    integration = await session.get(WhatsAppIntegrationModel, conversation["integration_id"])
    if not integration or integration.tipo != "openwa":
        raise HTTPException(404, "Arquivo não encontrado")
    try:
        credentials = json.loads(decrypt_secret(integration.credenciais_encriptadas))
    except (ValueError, SyntaxError):
        credentials = ast.literal_eval(decrypt_secret(integration.credenciais_encriptadas))
    base_url = str(credentials.get("base_url") or credentials.get("url") or "").rstrip("/")
    api_key = credentials.get("api_key") or credentials.get("key") or credentials.get("token")
    session_id = credentials.get("session_id") or credentials.get("session")
    chat_id = conversation.get("chat_id") or f'{conversation["telefone"]}@c.us'
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{base_url}/api/sessions/{session_id}/messages/{quote(chat_id, safe='')}/{quote(message['external_id'], safe='')}/media",
            headers={"X-API-Key": api_key},
        )
    if not response.is_success:
        raise HTTPException(404, "Arquivo não está mais disponível no OpenWA")
    filename = message.get("arquivo_nome") or "arquivo"
    disposition = "inline" if str(message["mime_type"]).startswith(("image/", "audio/", "video/")) else "attachment"
    return Response(
        content=response.content,
        media_type=message["mime_type"],
        headers={"Content-Disposition": f"{disposition}; filename*=UTF-8''{quote(filename)}"},
    )


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
    is_openwa_outgoing = bool(is_openwa and _is_openwa_outgoing(payload, data))
    openwa_chat_id = None
    if is_openwa:
        openwa_candidates = _openwa_phone_candidates(data, is_openwa_outgoing)
        openwa_chat_id = next(
            (str(value).strip() for value in openwa_candidates if isinstance(value, str) and "@" in value),
            None,
        )
    if is_evolution and evolution_key.get("fromMe"):
        return {"ok": True, "ignored": True, "reason": "from_me"}

    if is_openwa:
        # @lid is the routing identity required by OpenWA for replies, but it
        # is not the customer's phone number. Prefer the alternate phone JID
        # for the CRM and keep openwa_chat_id untouched for sending.
        telefone_candidatos = _openwa_phone_candidates(data, is_openwa_outgoing)
        telefone_origem = next(
            (
                value for value in telefone_candidatos
                if isinstance(value, str) and "@lid" not in value.lower()
            ),
            openwa_chat_id or "",
        )
    else:
        telefone_origem = (
            evolution_key.get("remoteJid")
            or evolution_key.get("remoteJidAlt")
            or data.get("from")
            or data.get("phone")
            or data.get("sender")
            or ""
        )
    telefone = str(telefone_origem).split("@", 1)[0].split(":", 1)[0]
    openwa_mime_type, openwa_filename, openwa_media_kind = _openwa_media_metadata(data) if is_openwa else (None, None, None)
    texto = str(
        evolution_message.get("conversation")
        or (evolution_message.get("extendedTextMessage") or {}).get("text")
        or (evolution_message.get("imageMessage") or {}).get("caption")
        or data.get("body")
        or data.get("text")
        or openwa_filename
        or ({"image": "Imagem", "sticker": "Figurinha", "video": "Vídeo", "audio": "Áudio", "ptt": "Áudio", "document": "Documento"}.get(openwa_media_kind))
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
    foto_perfil = conversation.get("foto_perfil") if conversation else None
    if is_openwa and openwa_chat_id and (not conversation or not foto_perfil or not nome_contato):
        openwa_name, openwa_photo = await _openwa_contact_details(integration, openwa_chat_id)
        if not nome_contato:
            nome_contato = openwa_name
        foto_perfil = openwa_photo or foto_perfil
    if not conversation:
        conversation = await mongo.create_conversation(integration_id, telefone, nome_contato, openwa_chat_id, foto_perfil)
    elif is_openwa:
        await mongo.update_contact(
            str(conversation["_id"]),
            nome_contato=nome_contato,
            chat_id=openwa_chat_id,
            foto_perfil=foto_perfil,
        )
    
    if conversation and conversation.get("status") == "humano":
        human_until = conversation.get("humano_ate")
        if not human_until:
            await mongo.update_status(str(conversation["_id"]), "humano")
        elif human_until <= datetime.now():
            await mongo.update_status(str(conversation["_id"]), "aberta")
            conversation["status"] = "aberta"
   
    try:
        await mongo.append_message(
            str(conversation["_id"]),
            external_id=external_id,
            direcao="saida" if is_openwa_outgoing else "entrada",
            tipo="arquivo" if openwa_mime_type else "text",
            conteudo=texto,
            arquivo_nome=openwa_filename,
            mime_type=openwa_mime_type,
        )
    except (KeyError, ValueError):
        raise HTTPException(404, "Conversa não encontrada")

    # Mensagens fromMe também representam respostas humanas feitas diretamente
    # no WhatsApp/OpenWA. Elas pertencem ao histórico, mas não devem acionar a IA.
    if is_openwa_outgoing:
        return {"ok": True, "conversation_id": str(conversation["_id"]), "outgoing": True}

    # A mídia fica disponível na inbox; sem um pipeline multimodal configurado,
    # ela não deve ser enviada ao agente como se o texto substituto fosse humano.
    if openwa_mime_type:
        return {"ok": True, "conversation_id": str(conversation["_id"]), "media": True}

    if conversation.get("status") == "humano" or _requests_human(texto) or _requests_course(texto):
        if conversation.get("status") != "humano":
            await mongo.update_status(str(conversation["_id"]), "humano")
        logger.info("Atendimento humano solicitado para o telefone final %s", telefone[-4:])
        return {"ok": True, "human_requested": True}

    if integration and integration.tipo in ("evolution", "openwa"):
        try:
            contexto = AtendimentoService(clientes, procedimentos, agendamentos, tempos_trabalho)
            resposta = await run_agent(texto, telefone, contexto)
            response_external_id = await _send_through_integration(integration, telefone, resposta, chat_id=openwa_chat_id)
            await mongo.append_message(str(conversation["_id"]), direcao="saida", tipo="text", conteudo=resposta, external_id=response_external_id)
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
