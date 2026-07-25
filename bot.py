import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PicklePersistence,
    filters,
)
from ai_handler import process_message

# Configura o logger para ajudar no debug
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Sites preferidos em cada tipo de busca. Sempre uma lista, nunca um domínio só:
# o include_domains da Tavily é preferência, não filtro rígido, e restringir demais
# faz a busca voltar vazia (ou escapar para sites sem relação nenhuma).
# /hoje precisa de canal de transmissão -> imprensa esportiva que cobre jogo a jogo.
DOMINIOS_HOJE = ["365scores.com", "ge.globo.com", "lance.com.br", "trivela.com.br"]
# /proximos precisa de calendário -> páginas de agenda/tabela. A ESPN mantém uma
# página de calendário por time (/futebol/time/calendario/_/id/<id>/<time>), que a
# busca encontra sozinha para qualquer clube.
# Sites oficiais de clube foram testados aqui e pioraram o resultado: a busca passava
# a devolver páginas de outros times e das categorias de base.
DOMINIOS_PROXIMOS = ["espn.com.br", "ge.globo.com", "lance.com.br"]

def acesso_liberado(update: Update) -> bool:
    """Verifica se o usuário tem permissão para usar o bot (bot privado)."""
    user_id = str(update.effective_user.id)
    allowed_id = os.getenv("ALLOWED_USER_ID")

    if allowed_id and allowed_id != "COLE_SEU_ID_DO_TELEGRAM_AQUI" and user_id != allowed_id:
        logger.warning(f"Tentativa de acesso bloqueada. ID: {user_id}")
        return False
    return True

async def responder_com_ia(update: Update, context: ContextTypes.DEFAULT_TYPE, pergunta: str,
                           dominios: list[str] | None = None):
    """Envia a pergunta para a IA mantendo o 'digitando...' ativo e responde ao usuário."""
    chat_id = update.effective_chat.id

    async def keep_typing():
        """Mantém o status de 'digitando' ativo no Telegram a cada 4 segundos."""
        try:
            while True:
                await context.bot.send_chat_action(chat_id=chat_id, action='typing')
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass

    # Inicia a tarefa visual de digitação em background
    typing_task = asyncio.create_task(keep_typing())

    try:
        # Roda o processamento da IA em uma Thread separada para não travar o bot inteiro
        loop = asyncio.get_running_loop()
        response_text = await loop.run_in_executor(None, process_message, pergunta, dominios)
    finally:
        # Quando a resposta chegar, para de mostrar 'digitando'
        typing_task.cancel()

    # Envia a resposta final
    await context.bot.send_message(
        chat_id=chat_id,
        text=response_text
    )

def time_escolhido(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """Retorna o time passado no comando ou, na falta dele, o time favorito salvo."""
    if context.args:
        return " ".join(context.args).strip()
    return context.user_data.get("time_favorito")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /start"""
    if not acesso_liberado(update):
        await update.message.reply_text("Acesso Negado: Este é um bot privado.")
        return

    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Olá, {user_name}! Eu sou o bot Onde Vai Jogar.\n"
        f"Pode me perguntar sobre os próximos jogos de futebol e eu te direi onde vão passar!\n\n"
        f"Dica: use /meutime para salvar seu time e depois é só mandar /hoje.\n"
        f"Digite /ajuda para ver tudo que eu faço."
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explica os comandos disponíveis."""
    if not acesso_liberado(update):
        await update.message.reply_text("Acesso Negado: Este é um bot privado.")
        return

    await update.message.reply_text(
        "⚽ Onde Vai Jogar - como usar\n\n"
        "/meutime Vasco - salva seu time favorito\n"
        "/meutime - mostra o time salvo\n"
        "/hoje - tem jogo hoje do seu time? onde passa?\n"
        "/proximos - os próximos jogos do seu time\n"
        "/ajuda - esta mensagem\n\n"
        "Os comandos /hoje e /proximos aceitam outro time direto, sem mudar o seu favorito. "
        "Exemplo: /hoje flamengo\n\n"
        "Você também pode perguntar do seu jeito, em texto normal. "
        "Exemplo: 'Onde vai passar o jogo do Vasco no sábado?'"
    )

async def meutime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Define ou mostra o time favorito do usuário."""
    if not acesso_liberado(update):
        await update.message.reply_text("Acesso Negado: Este é um bot privado.")
        return

    # Sem argumento: apenas mostra o que já está salvo
    if not context.args:
        favorito = context.user_data.get("time_favorito")
        if favorito:
            await update.message.reply_text(
                f"⚽ Seu time é o {favorito}.\n"
                f"Para trocar, mande: /meutime nome do time"
            )
        else:
            await update.message.reply_text(
                "Você ainda não escolheu um time.\n"
                "Mande assim: /meutime Vasco"
            )
        return

    time = " ".join(context.args).strip()
    context.user_data["time_favorito"] = time
    await update.message.reply_text(
        f"✅ Pronto! Seu time agora é o {time}.\n"
        f"Agora é só mandar /hoje ou /proximos que eu já sei de quem você está falando."
    )

async def hoje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Informa o jogo de hoje do time e onde assistir."""
    if not acesso_liberado(update):
        await update.message.reply_text("Acesso Negado: Este é um bot privado.")
        return

    time = time_escolhido(context)
    if not time:
        await update.message.reply_text(
            "Não sei qual é o seu time ainda.\n"
            "Mande /meutime Vasco para salvar, ou use /hoje flamengo para consultar um time direto."
        )
        return

    await responder_com_ia(
        update,
        context,
        f"O {time} joga hoje? Responda SOMENTE sobre o jogo de hoje: confronto, campeonato, "
        f"horário e onde assistir. Se não houver jogo hoje, diga apenas que não há jogo hoje "
        f"e não cite nenhum jogo futuro. "
        f"IMPORTANTE: ao chamar search_web, a query DEVE conter o nome do time e a expressão "
        f"'onde assistir' — sem isso a busca não devolve o canal de transmissão.",
        dominios=DOMINIOS_HOJE,
    )

async def proximos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista os próximos jogos do time."""
    if not acesso_liberado(update):
        await update.message.reply_text("Acesso Negado: Este é um bot privado.")
        return

    time = time_escolhido(context)
    if not time:
        await update.message.reply_text(
            "Não sei qual é o seu time ainda.\n"
            "Mande /meutime Vasco para salvar, ou use /proximos flamengo para consultar um time direto."
        )
        return

    await responder_com_ia(
        update,
        context,
        f"Quais são os próximos jogos do {time}? Liste até 5, com confronto, campeonato, "
        f"dia da semana, data e horário. Não preciso da transmissão aqui: só cite o canal "
        f"se a fonte trouxer.",
        dominios=DOMINIOS_PROXIMOS,
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa as mensagens de texto enviando para o Gemini"""
    if not acesso_liberado(update):
        await update.message.reply_text("Acesso Negado: Você não tem permissão para conversar com este bot.")
        return

    await responder_com_ia(update, context, update.message.text)

async def post_init(application: Application):
    """Registra os comandos no menu '/' do Telegram."""
    await application.bot.set_my_commands([
        BotCommand("hoje", "Tem jogo hoje? Onde passa?"),
        BotCommand("proximos", "Próximos jogos do meu time"),
        BotCommand("meutime", "Definir/ver meu time favorito"),
        BotCommand("ajuda", "Como usar o bot"),
    ])

if __name__ == '__main__':
    # Obtém o token do arquivo .env
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        logger.error("Token não encontrado. Verifique o arquivo .env!")
        exit(1)

    # Guarda o time favorito em disco. Em produção o caminho aponta para um volume
    # persistente, senão o dado se perde quando o contêiner é recriado.
    # update_interval menor que o padrão (60s) reduz a perda se o processo morrer de repente.
    persistence = PicklePersistence(
        filepath=os.getenv("PERSISTENCE_PATH", "bot_data.pkl"),
        update_interval=10,
    )

    # Inicializa a aplicação do bot
    application = (
        ApplicationBuilder()
        .token(token)
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )

    # Adiciona os handlers dos comandos
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('ajuda', ajuda))
    application.add_handler(CommandHandler('meutime', meutime))
    application.add_handler(CommandHandler('hoje', hoje))
    application.add_handler(CommandHandler('proximos', proximos))

    # Adiciona o handler para as mensagens de texto comuns
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    application.add_handler(text_handler)

    logger.info("Bot iniciado! Pressione Ctrl+C para encerrar.")

    # Roda o bot continuamente
    application.run_polling()
