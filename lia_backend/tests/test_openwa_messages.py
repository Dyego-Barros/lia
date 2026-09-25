from datetime import datetime, timedelta

import httpx

from app.api.routes.integracoes import (
    _is_openwa_outgoing,
    _openwa_history_get,
    _openwa_history_message,
    _openwa_media_metadata,
    _openwa_phone_candidates,
    _provider_message_id,
)
from app.infrastructure.database.mongo import _has_equivalent, _message_fingerprint


def test_extracts_openwa_message_id_from_nested_result():
    response = httpx.Response(
        200,
        json={"success": True, "result": {"id": "3EB0ABC"}},
    )

    assert _provider_message_id(response) == "3EB0ABC"


def test_returns_none_when_provider_does_not_return_message_id():
    response = httpx.Response(200, json={"success": True})

    assert _provider_message_id(response) is None


def test_recognizes_phone_message_as_outgoing_by_event():
    assert _is_openwa_outgoing({"event": "message.sent"}, {"fromMe": False}) is True


def test_outgoing_phone_candidates_do_not_use_account_number():
    data = {
        "from": "5511999999999@c.us",
        "to": "5521988888888@c.us",
        "chatId": "5521988888888@c.us",
    }

    candidates = _openwa_phone_candidates(data, outgoing=True)

    assert candidates[1] == "5521988888888@c.us"
    assert "5511999999999@c.us" not in candidates


def test_normalizes_human_outgoing_openwa_history_message():
    message = _openwa_history_message({
        "id": "false_5511999999999@c.us_ABC",
        "chatId": "5511999999999@c.us",
        "fromMe": True,
        "body": "Resposta feita pela atendente",
        "timestamp": 1_789_000_000,
        "type": "chat",
    })

    assert message is not None
    assert message["direcao"] == "saida"
    assert message["origem"] == "atendente_whatsapp"
    assert message["conteudo"] == "Resposta feita pela atendente"
    assert message["external_id"] == "false_5511999999999@c.us_ABC"


def test_normalizes_persisted_outgoing_direction_without_from_me():
    message = _openwa_history_message({
        "waMessageId": "outgoing-message",
        "direction": "outgoing",
        "body": "Resposta feita pela atendente",
        "timestamp": 1_789_000_000,
        "type": "text",
    })

    assert message is not None
    assert message["direcao"] == "saida"
    assert message["origem"] == "atendente_whatsapp"
    assert message["external_id"] == "outgoing-message"


def test_does_not_treat_string_false_from_me_as_outgoing():
    message = _openwa_history_message({
        "id": "incoming-message",
        "fromMe": "false",
        "body": "Mensagem da cliente",
        "timestamp": 1_789_000_000,
    })

    assert message is not None
    assert message["direcao"] == "entrada"


def test_ignores_history_entries_without_text():
    assert _openwa_history_message({"id": "reaction", "fromMe": True}) is None


def test_normalizes_received_openwa_document_without_caption():
    message = _openwa_history_message({
        "id": "document-message",
        "fromMe": False,
        "type": "document",
        "mimetype": "application/pdf; charset=binary",
        "filename": "contrato.pdf",
        "timestamp": 1_789_000_000,
    })

    assert message is not None
    assert message["direcao"] == "entrada"
    assert message["tipo"] == "arquivo"
    assert message["conteudo"] == "contrato.pdf"
    assert message["arquivo_nome"] == "contrato.pdf"
    assert message["mime_type"] == "application/pdf"


def test_extracts_nested_openwa_image_metadata():
    mime_type, filename, media_kind = _openwa_media_metadata({
        "type": "image",
        "message": {"imageMessage": {"mimetype": "image/webp", "fileName": "foto.webp"}},
    })

    assert (mime_type, filename, media_kind) == ("image/webp", "foto.webp", "image")


def test_detects_duplicate_from_live_and_persisted_history_with_different_ids():
    sent_at = datetime(2026, 9, 17, 22, 39, 49)
    stored = {"direcao": "saida", "conteudo": "Pulseira, anéis, brincos", "tipo": "text", "enviado_em": sent_at}
    fingerprints = {_message_fingerprint(stored)}
    candidate = {**stored, "external_id": "different-provider-id", "enviado_em": sent_at + timedelta(seconds=1)}

    assert _has_equivalent(fingerprints, candidate) is True


def test_preserves_repeated_message_outside_duplicate_window():
    sent_at = datetime(2026, 9, 17, 22, 39, 49)
    stored = {"direcao": "saida", "conteudo": "Ok", "tipo": "text", "enviado_em": sent_at}
    fingerprints = {_message_fingerprint(stored)}
    candidate = {**stored, "enviado_em": sent_at + timedelta(seconds=3)}

    assert _has_equivalent(fingerprints, candidate) is False


# def test_retries_openwa_history_after_rate_limit():
#     calls = 0

#     def handler(request: httpx.Request) -> httpx.Response:
#         nonlocal calls
#         calls += 1
#         if calls == 1:
#             return httpx.Response(429, headers={"Retry-After-short": "0"}, request=request)
#         return httpx.Response(200, json=[], request=request)

#     with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
#         response =  _openwa_history_get(client, "http://openwa/messages", headers={}, params={})

#     assert response.status_code == 200
#     assert calls == 2
