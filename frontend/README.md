# Game-Radar - Frontend

Este é o módulo de interface de usuário (Frontend) do sistema de recomendação de jogos Game-Radar. Desenvolvido em React + Vite.

## 🛠️ Pré-requisitos

* Docker

##  Como Iniciar

1. Clone o repositório e acesse a pasta do frontend:
```bash
git clone https://github.com/MateusPoddis/Game-Radar.git
cd Game-Radar/frontend
```

2. Construa a imagem e inicie o container
```bash
docker-compose up --build
```
ou
```bash
docker compose up --build
```

3. Baixe as dependências
```bash
docker exec -it frontend npm install react-router-dom
```

4. Acesse a aplicação em [http://localhost:5173](http://localhost:5173)

Novas dependências são baixadas com:
```bash
docker exec -it frontend npm install <nome-do-pacote>
```

Pare a aplicação com:
```bash
docker-compose down
```
ou
```bash
docker compose down
```
