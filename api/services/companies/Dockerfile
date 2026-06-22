FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /workspace

COPY pyproject.toml uv.lock ./
COPY shared/pyproject.toml shared/pyproject.toml
COPY services/companies/pyproject.toml services/companies/pyproject.toml
COPY shared/src shared/src
COPY services/companies/src services/companies/src

RUN uv export \
    --project companies \
    --frozen \
    --package companies \
    --no-dev \
    --no-emit-workspace \
    --format requirements.txt \
    --output-file /tmp/requirements.txt

FROM public.ecr.aws/lambda/python:3.12

COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY services/companies/src/ ${LAMBDA_TASK_ROOT}/
COPY shared/src/ ${LAMBDA_TASK_ROOT}/

CMD ["companies.handler.lambda_handler"]