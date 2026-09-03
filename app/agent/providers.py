"""Configuração dos provedores de LLM usados pelo agente.

Todos os provedores expõem uma API compatível com o cliente OpenAI. Isso
permite manter o mesmo conjunto de ferramentas e trocar de provedor apenas
quando houver uma falha temporária no provedor anterior.
"""

import logging
import os
from collections.abc import Sequence
from typing import Any

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


_DEFAULT_ORDER = ("groq", "ollama", "openai")
_TRANSIENT_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def _provider_order() -> list[str]:
    configured = os.getenv("AI_PROVIDER_ORDER", ",".join(_DEFAULT_ORDER))
    return [item.strip().lower() for item in configured.split(",") if item.strip()]


def _env_provider_config(name: str) -> dict[str, Any] | None:
    configurations = {
        "ollama": {
            "api_key": os.getenv("OLLAMA_API_KEY"),
            "model": os.getenv("OLLAMA_MODEL", "gpt-oss:20b-cloud"),
            "base_url": os.getenv("OLLAMA_BASE_URL", "https://ollama.com/api"),
        },
        "groq": {
            "api_key": os.getenv("GROQ_API_KEY"),
            "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            "base_url": os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        },
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": os.getenv("OPENAI_MODEL", "gpt-oss-20b"),
            "base_url": os.getenv("OPENAI_BASE_URL"),
        },
    }
    config = configurations.get(name)
    if not config or not config["api_key"]:
        return None
    return config


def _build_models(tools: Sequence[Any], configurations: list[tuple[str, dict[str, Any]]]) -> list[tuple[str, Any]]:
    """Cria os modelos configurados na ordem de preferência.

    O primeiro provedor disponível é usado normalmente. Os demais ficam
    preparados para fallback em caso de erro temporário.
    """
    models: list[tuple[str, Any]] = []
    for name, config in configurations:
        kwargs = {
            "model": config["model"],
            "temperature": 0.5,
            "api_key": config["api_key"],
            "timeout": 30,
            "max_retries": 1,
        }
        if config["base_url"]:
            kwargs["base_url"] = config["base_url"]
        models.append((name, ChatOpenAI(**kwargs).bind_tools(tools)))

    if not models:
        raise RuntimeError(
            "Nenhum provedor de IA configurado. Defina GROQ_API_KEY, "
            "OLLAMA_API_KEY ou OPENAI_API_KEY."
        )
    return models


def build_provider_models_from_env(tools: Sequence[Any]) -> list[tuple[str, Any]]:
    configurations = [(name, config) for name in _provider_order() if (config := _env_provider_config(name))]
    if not configurations:
        raise RuntimeError("Nenhum provedor de IA configurado. Defina GROQ_API_KEY, OLLAMA_API_KEY ou OPENAI_API_KEY.")
    return _build_models(tools, configurations)


async def build_provider_models(tools: Sequence[Any]) -> list[tuple[str, Any]]:
    """Carrega modelos ativos do PostgreSQL por prioridade, com fallback para o .env."""
    from sqlalchemy import select
    from app.infrastructure.database.db import AsyncSessionLocal
    from app.infrastructure.database.models.models import AIIntegrationModel
    from app.infrastructure.security.secrets import decrypt_secret

    async with AsyncSessionLocal() as session:
        items = (await session.execute(select(AIIntegrationModel).where(AIIntegrationModel.ativo.is_(True)).order_by(AIIntegrationModel.prioridade, AIIntegrationModel.id))).scalars().all()
        configurations: list[tuple[str, dict[str, Any]]] = []
        for item in items:
            try:
                configurations.append((item.nome, {"api_key": decrypt_secret(item.api_key_encriptada), "model": item.modelo, "base_url": item.base_url}))
            except Exception:
                logger.exception("Não foi possível descriptografar o modelo de IA %s", item.id)
    if configurations:
        return _build_models(tools, configurations)
    return build_provider_models_from_env(tools)


def is_transient_provider_error(error: Exception) -> bool:
    """Indica se vale tentar o próximo provedor.

    Erros de credencial ou payload inválido não acionam fallback, pois repetir
    a mesma requisição em outro provedor esconderia um erro de configuração.
    """
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        response = getattr(error, "response", None)
        status_code = getattr(response, "status_code", None)
    if status_code is not None:
        if status_code in _TRANSIENT_STATUS_CODES:
            return True
        # Um modelo pode ser removido ou ficar indisponível em apenas um
        # provedor. Nesse caso, tente o próximo modelo configurado.
        if status_code == 404:
            message = f"{type(error).__name__} {error}".lower()
            return "model" in message and any(
                marker in message
                for marker in ("not found", "not exist", "does not exist", "model_not_found")
            )
        return False

    return isinstance(error, (TimeoutError, ConnectionError)) or any(
        marker in type(error).__name__.lower()
        for marker in ("timeout", "connect", "network", "temporarily")
    )


def log_provider_failure(provider: str, error: Exception) -> None:
    """Registra somente o tipo do erro, sem expor prompt ou credenciais."""
    logger.warning(
        "Provedor de IA temporariamente indisponível: %s (%s)",
        provider,
        type(error).__name__,
    )
