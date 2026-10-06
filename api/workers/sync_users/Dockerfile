FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /workspace

COPY pyproject.toml uv.lock ./
COPY shared/pyproject.toml shared/pyproject.toml
COPY workers/sync_users/pyproject.toml workers/sync_users/pyproject.toml
COPY shared/src shared/src
COPY workers/sync_users/src workers/sync_users/src

RUN uv export \
    --project sync_users \
    --frozen \
    --package sync_users \
    --no-dev \
    --no-emit-workspace \
    --format requirements.txt \
    --output-file /tmp/requirements.txt

FROM public.ecr.aws/lambda/python:3.12

COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY workers/sync_users/src/ ${LAMBDA_TASK_ROOT}/
COPY shared/src/ ${LAMBDA_TASK_ROOT}/