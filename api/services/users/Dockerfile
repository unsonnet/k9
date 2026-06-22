FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /workspace

COPY pyproject.toml uv.lock ./
COPY shared/pyproject.toml shared/pyproject.toml
COPY services/users/pyproject.toml services/users/pyproject.toml
COPY shared/src shared/src
COPY services/users/src services/users/src

RUN uv export \
    --project users \
    --frozen \
    --package users \
    --no-dev \
    --no-emit-workspace \
    --format requirements.txt \
    --output-file /tmp/requirements.txt

FROM public.ecr.aws/lambda/python:3.12

COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY services/users/src/ ${LAMBDA_TASK_ROOT}/
COPY shared/src/ ${LAMBDA_TASK_ROOT}/

CMD ["users.handler.lambda_handler"]