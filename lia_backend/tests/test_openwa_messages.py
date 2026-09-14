import httpx

from app.api.routes.integracoes import _openwa_history_message, _provider_message_id


def test_extracts_openwa_message_id_from_nested_result():
    response = httpx.Response(
        200,
        json={"success": True, "result": {"id": "3EB0ABC"}},
    )

    assert _provider_message_id(response) == "3EB0ABC"


def test_returns_none_when_provider_does_not_return_message_id():
    response = httpx.Response(200, json={"success": True})

    assert _provider_message_id(response) is None


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
    assert message["conteudo"] == "Resposta feita pela atendente"
    assert message["external_id"] == "false_5511999999999@c.us_ABC"


def test_ignores_history_entries_without_text():
    assert _openwa_history_message({"id": "reaction", "fromMe": True}) is None
