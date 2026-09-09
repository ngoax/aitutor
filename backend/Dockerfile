# syntax=docker/dockerfile:1

FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV HF_HOME=/opt/hf
COPY app/rag/embeddings.py /tmp/prefetch/embeddings.py
RUN /app/.venv/bin/python -c "\
import sys; sys.path.insert(0, '/tmp/prefetch'); \
from embeddings import get_embedding_model; get_embedding_model()"

RUN /app/.venv/bin/python -c "\
from huggingface_hub import hf_hub_download; \
hf_hub_download('xberg-io/layout-models', 'rtdetr/model.onnx'); \
hf_hub_download('xberg-io/layout-models', 'tatr/model.onnx')"


FROM python:3.13-slim-bookworm AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 app

# config.py derives data_dir from the repo layout, which does not exist here.
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    HF_HOME=/opt/hf \
    DATA_DIR=/data

RUN mkdir -p /data && chown app:app /data

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /opt/hf /opt/hf
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app app ./app

USER app
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
