<h1 align="center">
  ⚽ Onde Vai Jogar Bot
</h1>

<p align="center">
  <a href="#-sobre-o-projeto">Sobre</a> •
  <a href="#-funcionalidades">Funcionalidades</a> •
  <a href="#-tecnologias">Tecnologias</a> •
  <a href="#-como-executar">Como Executar</a> •
  <a href="#-deploy">Deploy</a> •
  <a href="#-licença">Licença</a>
</p>

<p align="center">
  Um bot de Telegram focado em responder de forma rápida e inteligente a uma das perguntas mais comuns do torcedor brasileiro: <strong>"Onde vai passar o jogo?"</strong>
</p>

---

## 📌 Sobre o Projeto

O **Onde Vai Jogar** é um assistente virtual Open Source construído para o Telegram. Diferente de bots tradicionais baseados em comandos fixos, este projeto utiliza a Inteligência Artificial do Google Gemini integrada à API de buscas Tavily. Isso permite que o usuário faça perguntas em linguagem natural e receba dados precisos e atualizados em tempo real sobre transmissões televisivas e horários de partidas de futebol.

### 🎯 A Motivação (De Torcedor para Torcedor)
A ideia central do projeto nasceu de uma dor real: como torcedor do **Vasco da Gama**, eu sentia uma imensa dificuldade em descobrir de forma rápida onde e que horas meu Vascão ia jogar. A rotina de ter que abrir o Google, pesquisar a tabela, procurar a emissora ou o streaming toda vez antes de uma partida era exaustiva. 

Este bot foi criado para facilitar a vida de todos os torcedores. Com uma simples mensagem no Telegram, você recebe exatamente a informação que importa, sem enrolação.

## ✨ Funcionalidades

- **Linguagem Natural:** O usuário pode perguntar livremente (ex: *"Vai ter jogo do Vasco hoje? Se sim, em qual canal?"*).
- **Dados em Tempo Real:** Conectado à internet via [Tavily Search API](https://tavily.com/), garantindo que informações sobre transmissões, cancelamentos ou horários de última hora sejam capturados corretamente.
- **Prevenção de Alucinação:** O modelo de IA é configurado de forma estrita para não tentar adivinhar resultados. Ele baseia sua resposta 100% no conteúdo das notícias e tabelas encontradas no momento da pergunta.
- **Concorrência Assíncrona:** Arquitetura pensada para não travar. O processamento da inteligência artificial ocorre em *Threads* secundárias (`run_in_executor`), enquanto o bot avisa visualmente o usuário ("Digitando...") em tempo real de forma assíncrona.

## 🛠 Tecnologias

As seguintes ferramentas foram utilizadas na construção do projeto:

- [Python 3.10+](https://www.python.org/)
- [python-telegram-bot](https://python-telegram-bot.org/) - Interação com a API do Telegram.
- [Google Generative AI](https://ai.google.dev/) - Modelo `gemini-3.1-flash-lite` para orquestração e compreensão de texto.
- [Tavily Python](https://tavily.com/) - Mecanismo de busca Web em tempo real para Agentes de Inteligência Artificial.

## 🚀 Como Executar

Antes de começar, você precisará ter o [Git](https://git-scm.com) e o [Python](https://python.org) instalados em sua máquina. Você também precisará criar as seguintes chaves de API:
- Token do Bot no [BotFather](https://t.me/botfather) (Telegram)
- Chave de API do [Google AI Studio](https://aistudio.google.com/)
- Chave de API do [Tavily](https://tavily.com/)

### 1. Clonando o Repositório
```bash
$ git clone https://github.com/feliperelvas/onde_vai_jogar.git
$ cd onde_vai_jogar
```

### 2. Configurando o Ambiente
Crie um arquivo chamado `.env` na raiz do projeto contendo as suas chaves geradas:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
TAVILY_API_KEY=sua_chave_tavily_aqui
ALLOWED_USER_ID=seu_id_do_telegram_aqui
```

### 3. Instalando as Dependências
```bash
$ python -m venv venv
# Ative o ambiente virtual (Windows):
$ venv\Scripts\activate
# Ative o ambiente virtual (Linux/Mac):
$ source venv/bin/activate

$ pip install -r requirements.txt
```

### 4. Rodando o Bot
```bash
$ python bot.py
```

## ☁️ Deploy (Hospedagem Gratuita 24/7)

O bot foi projetado para rodar perfeitamente em serviços de nuvem modernos. Recomendamos a plataforma **JustRunMy.App** pelo seu plano gratuito que suporta processos de *background* contínuos (Polling), sem colocar sua aplicação para "dormir" por inatividade.

1. Crie uma conta gratuita no [JustRunMy.App](https://justrunmy.app/) (não exige cartão de crédito).
2. Selecione a opção de deploy via **GitHub** e conecte o seu repositório.
3. O plano gratuito inclui 1 contêiner (0.15 vCPU e 250MB RAM), o que é mais do que suficiente para o bot.
4. Vá até a seção de **Environment Variables** (Variáveis de Ambiente) e adicione as chaves de segurança criadas no passo anterior:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `TAVILY_API_KEY`
   - `ALLOWED_USER_ID`
5. Confirme o deploy. O servidor instalará as dependências via *buildpack* automaticamente e executará o `bot.py` em segundo plano para sempre!

## 📝 Licença

Este projeto está sob a licença MIT. Sinta-se à vontade para clonar, modificar e distribuir.
