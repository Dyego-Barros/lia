FROM python:3.14-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN apk add --no-cache build-base libffi-dev openssl-dev
RUN python -m venv "$VIRTUAL_ENV"
RUN pip install --upgrade pip
RUN pip install alembic asyncpg fastapi httpx cryptography PyJWT langchain-core langchain-groq langchain-openai langgraph motor psycopg2-binary python-dotenv sqlalchemy uvicorn

FROM python:3.14-alpine AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
RUN apk add --no-cache libffi openssl libpq
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "alembic -c /app/alembic.ini upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
