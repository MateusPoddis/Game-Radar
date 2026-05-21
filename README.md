# Sistema Distribuído de Recomendação de Jogos (RAG + MCP)

Este projeto consiste em um sistema distribuído de recomendação personalizada de jogos eletrônicos. A arquitetura foi desenhada sob o paradigma de microsserviços para unir o poder de modelos de linguagem de código aberto (LLMs), recuperação de contexto semântico via RAG (Retrieval-Augmented Generation) e integração dinâmica com APIs de mercado através do protocolo MCP (Model Context Protocol).

---

## 1. Problema Escolhido

Sistemas de recomendação tradicionais de e-commerce e plataformas de jogos frequentemente sofrem com duas limitações principais:
1. **Rigidez Algorítmica:** Filtros baseados puramente em tags estruturadas (ex: "Ação", "RPG") falham em capturar nuances subjetivas expressas pelos usuários (ex: *"Quero um jogo com uma atmosfera melancólica, foco em narrativa e mecânicas de plantio que não seja excessivamente punitivo"*).
2. **Isolamento de Modelos de IA:** Modelos de Linguagem (LLMs) possuem conhecimento estático limitado à sua data de treinamento. Eles não conseguem consultar preços em tempo real, verificar promoções ativas em múltiplas lojas ou saber se o usuário já possui o jogo em sua biblioteca.

**A Solução:** Este sistema resolve o problema unindo bancos de dados relacionais (para dados cadastrais e estruturados), um banco vetorial (RAG) para armazenar informações sobre jogos, e um ecossistema MCP para atuar como os braços e olhos da IA no mundo real, consultando preços ao vivo.

---

## 2. Arquitetura Proposta

A arquitetura adota o padrão de microsserviços distribuídos, garantindo o desacoplamento das responsabilidades, facilidade de manutenção e escalabilidade independente de cada componente. 

O ecossistema é totalmente conteinerizado, isolando a camada de controle de acesso e dados transacionais (construída sobre a robustez do ecossistema Java/Spring) da camada de inteligência artificial e integração de ferramentas (construída sobre a flexibilidade do ecossistema Python e IA).

---

## 3. Componentes do Sistema

O sistema é dividido nos seguintes módulos independentes:

* **Frontend (React):** Interface SPA (Single Page Application) responsável por coletar as preferências do usuário através de formulários interativos, renderizar o catálogo de recomendações com comparativos de preços e coletar feedbacks textuais e numéricos pós-indicação.
* **API Gateway (FastAPI):** Ponto de entrada único para o Frontend. É responsável por interceptar todas as requisições, validar a autenticidade dos tokens de acesso e rotear as chamadas para seus respectivos microsserviços de destino.
* **Módulo de Login & Autenticação (Spring Boot):** Serviço crítico de segurança isolado. Responsável por autenticar as credenciais do usuário, gerenciar a segurança criptográfica e emitir tokens JWT (JSON Web Tokens) assinados.
* **Módulo CRUD de Usuários (Spring Boot):** Gerencia os dados cadastrais, informações de perfil e configurações de conta do usuário.
* **Banco de Dados Relacional (PostgreSQL):** Instância dedicada para os serviços Spring Boot, garantindo a consistência e integridade das tabelas de usuários, credenciais, jogos e relacionamentos transacionais.
* **Módulo de Inteligência Artificial (Ollama + LangChain):** O núcleo cognitivo do sistema. Orquestra a lógica de recomendação recebendo a requisição do Gateway, consultando a memória semântica e acionando as ferramentas necessárias para construir o prompt final.
* **Banco de Dados Vetorial (RAG):** Armazena os embeddings de jogos buscados pela API RAWG.
* **Servidor MCP (Python SDK):** Atua como o provedor de ferramentas para a IA. Ele expõe funções padronizadas para  comparar preços em tempo real através da API CheapShark.

---

## 4. Fluxo de Dados

O ciclo de vida de uma requisição de recomendação segue o fluxo abaixo:

1.  **Autenticação:** O usuário realiza o login pelo Frontend. O `Módulo de Login` valida as credenciais no `PostgreSQL` e devolve um token JWT. O Frontend armazena este token para as próximas requisições.
2.  **Requisição de Recomendação:** O usuário preenche o formulário de preferências atuais e clica em buscar. A requisição viaja com o JWT até o `API Gateway`, que valida o token e a redireciona para o `Módulo de IA`.
3.  **Recuperação de Contexto (RAG):** O `Módulo de IA` intercepta a requisição e, antes de consultar o modelo, faz uma busca de similaridade no `Banco Vetorial (RAG)` usando as informações passadas pelo formulário.
4.  **Consulta de Ferramentas (MCP):** Com os jogos buscados, o framework `LangChain` percebe a necessidade de dados dinâmicos de mercado e aciona o `Servidor MCP`. O MCP faz chamadas externas para as API CheapShark buscando informações atuais dos jogos.
5.  **Geração da Resposta:** O `LangChain` injeta o contexto do RAG e os dados vivos do MCP dentro de um prompt estruturado e o envia para o modelo de linguagem local rodando no `Ollama`. O modelo processa e gera uma recomendação textual altamente personalizada e humanizada.
6.  **Exibição e Feedback Loop:** A resposta retorna pelo Gateway até o Frontend. O usuário pode interagir com o resultado dando feedback sobre os jogos recomendados.

---

## 5. Tecnologias Utilizadas

* **Frontend:** React (TypeScript) - Escolhido pela reatividade e ecossistema robusto para gerenciamento de estados de formulários e componentes visuais.
* **API Gateway:** FastAPI (Python) - Escolhido pela sua altíssima performance, tipagem nativa com Pantic e facilidade de criação de middlewares de roteamento rápidos.
* **Backend Transacional (Login e CRUDs):** Spring Boot (Java 17+) - Escolhido pela maturidade corporativa, segurança nativa (Spring Security) e isolamento robusto de processos críticos de persistência de dados.
* **Banco de Dados Relacional:** PostgreSQL - Líder em código aberto para persistência ACID, garantindo integridade absoluta para tabelas de usuários e relacionamentos estruturados.
* **Orquestração de IA:** LangChain (Python) - Framework padrão de mercado para criar pipelines complexos de IA, gerenciar prompts e conectar agentes a ferramentas e memórias externas.
* **Motor de LLM:** Ollama - Permite a execução local de modelos de linguagem avançados (como LLaMA 3 ou Mistral) em contêineres Docker, garantindo privacidade de dados e custo zero por token em ambiente de desenvolvimento.
* **Integração de Contexto:** Protocolo MCP (Model Context Protocol) via Python SDK - Tecnologia de vanguarda que padroniza a injeção de contexto e chamadas de ferramentas (*tool calling*) para LLMs, eliminando acoplamentos rígidos no código de IA.
* **Infraestrutura e Orquestração:** Docker & Docker Compose - Utilizados para empacotar cada módulo em ambientes isolados, permitindo que ferramentas complexas (como o PostgreSQL, o Ollama e os microsserviços Spring/FastAPI) sejam baixadas, configuradas e inicializadas de forma integrada com um único comando.
