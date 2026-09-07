FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt \
    && pip install langchain-zhipu==4.1.8 --no-deps \
    && python -m spacy download en_core_web_md \
    && python -m spacy download zh_core_web_sm

COPY . .

RUN chmod +x docker/entrypoint.sh \
    && mkdir -p storage/memory_file storage/kb_file storage/image_file load_model

EXPOSE 8182

ENTRYPOINT ["docker/entrypoint.sh"]
