FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini start.sh ./
COPY alembic ./alembic
COPY src ./src

RUN useradd --create-home --shell /usr/sbin/nologin donabe
USER donabe

EXPOSE 8000
CMD ["sh", "start.sh"]
