FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt /tmp/requirements.txt

RUN pip install \
    --no-cache-dir \
    --no-deps \
    --require-hashes \
    -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY src/ ${LAMBDA_TASK_ROOT}/
