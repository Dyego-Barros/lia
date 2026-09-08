import os
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.agent.providers import _env_provider_config, _provider_order, build_provider_models
from app.api.routes.auth import get_current_user
from app.api.routes.whatsapp import _send_message as send_meta_message
from app.api.routes.ultramsg import _send_message as send_ultramsg_message
from app.api.schemas.configuracoes import AITestRequest, WhatsAppTestRequest

router = APIRouter(prefix="/configuracoes", tags=["Configurações"], dependencies=[Depends(get_current_user)])


@router.get("/whatsapp/status")
async def whatsapp_status():
    meta = bool(os.getenv("PHONE_NUMBER_ID", "").strip() and os.getenv("ZAP_TOKEN", "").strip())
    ultramsg = bool(os.getenv("ULTRAMSG_INSTANCE_ID", "").strip() and os.getenv("ULTRAMSG_TOKEN", "").strip())
    return {"providers": [{"id": "meta", "nome": "WhatsApp Cloud API", "configurado": meta, "webhook_configurado": bool(os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip())}, {"id": "ultramsg", "nome": "UltraMsg", "configurado": ultramsg, "webhook_configurado": bool(os.getenv("ULTRAMSG_WEBHOOK_SECRET", "").strip())}], "observacao": "Credenciais são mantidas no ambiente e nunca retornadas pela API."}


@router.post("/whatsapp/testar")
async def testar_whatsapp(payload: WhatsAppTestRequest):
    try:
        if payload.provider == "ultramsg": await send_ultramsg_message(payload.telefone, payload.mensagem)
        elif payload.provider == "meta": await send_meta_message(payload.telefone, payload.mensagem)
        else: raise HTTPException(400, "Provider WhatsApp inválido")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "Falha ao enviar mensagem de teste") from exc
    return {"ok": True, "provider": payload.provider, "mensagem": "Mensagem de teste enviada."}


@router.get("/ia/status")
async def ia_status():
    providers = []
    for name in _provider_order():
        config = _env_provider_config(name)
        providers.append({"id": name, "configurado": bool(config), "modelo": config["model"] if config else None, "base_url": config["base_url"] if config else None})
    return {"ordem": _provider_order(), "providers": providers}


@router.post("/ia/testar")
async def testar_ia(payload: AITestRequest):
    started = time.perf_counter()
    try:
        models = await build_provider_models([])
        provider, model = models[0]
        response = await model.ainvoke(payload.mensagem)
        answer = getattr(response, "content", str(response))
        return {"ok": True, "provider": provider, "resposta": answer, "duracao_ms": round((time.perf_counter() - started) * 1000)}
    except Exception as exc:
        raise HTTPException(503, "Nenhum provider de IA respondeu ao teste") from exc


@router.get("/ia/metricas")
async def ia_metricas():
    configured = [name for name in _provider_order() if _env_provider_config(name)]
    return {"providers_configurados": len(configured), "providers": configured, "observacao": "Métricas detalhadas serão persistidas após ativar o registro de chamadas."}
