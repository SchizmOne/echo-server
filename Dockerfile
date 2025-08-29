FROM python:3.10-alpine

WORKDIR /app

COPY src/ ./src
COPY echoserver_client.py ./echoserver_client.py

RUN pip install --no-cache-dir -e src && pip check
RUN python3 -m unittest discover -v src/

ENTRYPOINT ["python", "echoserver_client.py"]