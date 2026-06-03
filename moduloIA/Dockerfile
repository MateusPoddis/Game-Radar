# Usa uma imagem oficial do Python, versão leve (slim)
FROM python:3.11-slim

# Evita que o Python grave arquivos .pyc e força os logs a aparecerem no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do seu servidor MCP para o container
COPY server.py .

# Comando padrão executado ao iniciar o container
CMD ["python", "server.py"]