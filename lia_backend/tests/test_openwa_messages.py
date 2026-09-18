import httpx

from app.api.routes.integracoes import (
    _is_openwa_outgoing,
    _openwa_history_message,
    _openwa_media_metadata,
    _openwa_phone_candidates,
    _provider_message_id,
)


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
