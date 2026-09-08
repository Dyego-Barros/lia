# Agente de atendimento

## Provedores de IA

O agente pode usar três provedores compatíveis com a API OpenAI. A ordem
 padrão é:

```text
Groq -> Ollama Cloud -> OpenAI
```

Configure as chaves no `.env` usando `.env.example` como referência. O agente
usa o primeiro provedor configurado e só tenta o próximo quando ocorre um
erro temporário, como limite `429`, timeout ou indisponibilidade `5xx`. Erros
de credencial, modelo inválido e payload inválido não são mascarados por um
fallback.

Exemplo:

```env
AI_PROVIDER_ORDER=groq,ollama,openai
GROQ_API_KEY=sua-chave
OLLAMA_API_KEY=sua-chave
OPENAI_API_KEY=sua-chave
```

As ferramentas de agendamento são compartilhadas entre os provedores. A
idempotência, a validação de disponibilidade e a confirmação do cliente
continuam sendo executadas pelo backend, independentemente do modelo usado.
## MongoDB para conversas WhatsApp

As conversas da inbox são armazenadas em `whatsapp_conversations` no MongoDB.
Cada documento representa um telefone e possui o array `mensagens`. O array é
limitado por `MONGODB_MAX_MESSAGES` (padrão: 2000) para evitar documentos
grandes demais; o histórico antigo continua no PostgreSQL até a migração.

Configure `MONGODB_URL`, `MONGODB_DATABASE` e `MONGODB_MAX_MESSAGES`. Para
copiar o histórico já existente, com PostgreSQL e Mongo disponíveis, execute:

```bash
python scripts/migrate_whatsapp_to_mongodb.py
```

## OpenWA em containers

O `docker-compose.yaml` inclui a imagem oficial `rmyndharis/openwa:0.23.3` na
rede interna. O serviço `api` chama `http://openwa:2785/api/sessions/<sessionId>`
e o OpenWA entrega mensagens em `http://api:8000/webhooks/openwa/<secret>`.
Nenhuma porta do
OpenWA ou da API é publicada; o frontend faz proxy das chamadas para `/api`.

Defina `OPENWA_API_KEY` (com pelo menos 32 caracteres) e
`OPENWA_WEBHOOK_SECRET` no `.env`. Depois de iniciar, crie uma sessão pela API
interna do OpenWA, inicie-a e leia o QR Code pelo endpoint `/api/sessions/<id>/qr`.
O `<id>` retornado pelo OpenWA é o `session_id` usado nas credenciais da
integração:

```json
{"base_url":"http://openwa:2785","api_key":"mesma-chave-de-OPENWA_API_KEY","session_id":"id-da-sessao-openwa"}
```

Use o mesmo valor de `OPENWA_WEBHOOK_SECRET` no campo Token do webhook e
registre no OpenWA o webhook `http://api:8000/webhooks/openwa/<secret>` para o
evento `message.received`. O OpenWA é uma automação não oficial do WhatsApp;
avalie as limitações e o risco de bloqueio da conta antes de usar em produção.
