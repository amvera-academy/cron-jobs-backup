FROM python:3.11-slim-bookworm

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg; \
    install -d -m 0755 /etc/apt/keyrings; \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
      | gpg --dearmor -o /etc/apt/keyrings/pgdg.gpg; \
    echo "deb [signed-by=/etc/apt/keyrings/pgdg.gpg] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
      > /etc/apt/sources.list.d/pgdg.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends postgresql-client-17; \
    rm -rf /var/lib/apt/lists/*; \
    pg_dump --version

RUN pip install --no-cache-dir requests==2.31.0

WORKDIR /app
COPY main.py /app/main.py

CMD ["python", "main.py"]
