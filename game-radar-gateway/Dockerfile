FROM python:3.11-slim

WORKDIR /app

# Instala as dependências primeiro para aproveitar o cache das camadas do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY ./app ./app

# Expõe a porta padrão do FastAPI
EXPOSE 8080

# Inicializa o Uvicorn apontando para a porta exposta
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]