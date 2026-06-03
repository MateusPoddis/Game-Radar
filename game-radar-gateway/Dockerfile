FROM python:3.12-slim

WORKDIR /app

# Instala dependências usando cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY . .

EXPOSE 8080

# 0.0.0.0 permite que o contêiner receba chamadas de fora dele
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]