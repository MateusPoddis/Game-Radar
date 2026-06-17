
# Dockerfile — Módulo IA + RAG
FROM python:3.11-slim

# Evita arquivos desnecessários e força os logs no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências do sistema (necessárias para o chromadb compilar)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python primeiro (cache de layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Porta onde o FastAPI vai escutar
EXPOSE 8002

# Comando padrão: sobe o orquestrador de IA
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]