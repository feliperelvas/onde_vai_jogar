import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from ai_handler import process_message

# Configura o logger para ajudar no debug
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /start"""
    user_id = str(update.effective_user.id)
    allowed_id = os.getenv("ALLOWED_USER_ID")
    
    if allowed_id and allowed_id != "COLE_SEU_ID_DO_TELEGRAM_AQUI" and user_id != allowed_id:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Acesso Negado: Este é um bot privado.")
        return

    user_name = update.effective_user.first_name
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Olá, {user_name}! Eu sou o bot Onde Vai Jogar.\nPode me perguntar sobre os próximos jogos de futebol e eu te direi onde vão passar!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa as mensagens de texto enviando para o Gemini"""
    user_id = str(update.effective_user.id)
    allowed_id = os.getenv("ALLOWED_USER_ID")
    
    if allowed_id and allowed_id != "COLE_SEU_ID_DO_TELEGRAM_AQUI" and user_id != allowed_id:
        logger.warning(f"Tentativa de acesso bloqueada. ID: {user_id}")
        await update.message.reply_text("Acesso Negado: Você não tem permissão para conversar com este bot.")
        return

    user_message = update.message.text
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
        response_text = await loop.run_in_executor(None, process_message, user_message)
    finally:
        # Quando a resposta chegar, para de mostrar 'digitando'
        typing_task.cancel()
    
    # Envia a resposta final
    await context.bot.send_message(
        chat_id=chat_id,
        text=response_text
    )

if __name__ == '__main__':
    # Obtém o token do arquivo .env
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("Token não encontrado. Verifique o arquivo .env!")
        exit(1)

    # Inicializa a aplicação do bot
    application = ApplicationBuilder().token(token).build()
    
    # Adiciona o handler para o comando /start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    
    # Adiciona o handler para as mensagens de texto comuns
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    application.add_handler(text_handler)
    
    logger.info("Bot iniciado! Pressione Ctrl+C para encerrar.")
    
    # Roda o bot continuamente
    application.run_polling()
