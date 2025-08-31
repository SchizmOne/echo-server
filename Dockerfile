FROM python:3.10-alpine AS builder

WORKDIR /build

COPY requirements.txt pyproject.toml setup.cfg ./
RUN pip install --upgrade pip setuptools wheel build

COPY echoserver/ ./echoserver
RUN pip install --no-cache-dir -e .

COPY tests/ ./tests/
RUN python -m unittest discover -v \
    && python -m build .

FROM python:3.10-alpine AS release

WORKDIR /app

COPY --from=builder /build/dist/*.whl ./dist/
RUN pip install --no-cache-dir --find-links dist/ dist/*.whl \
    && pip check

COPY client.py ./client.py

ENTRYPOINT ["python"]