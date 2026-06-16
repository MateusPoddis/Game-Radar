# Usa uma imagem oficial do Python, versão leve (slim)
FROM python:3.11-slim

# Evita arquivos desnecessários e força os logs no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala TODAS as dependências (IA + MCP) de uma vez
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da pasta (main.py, server.py, etc) para o container
COPY . .

# Expõe a porta do Orquestrador
EXPOSE 8000

# O Orquestrador é quem assume o controle do container!
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]