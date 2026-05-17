import os
import logging
import datetime
from tavily import TavilyClient
import google.generativeai as genai

logger = logging.getLogger(__name__)

def get_model():
    """Configura o Gemini e a ferramenta de busca."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "COLE_SUA_CHAVE_AQUI":
        raise ValueError("Chave de API do Gemini não configurada.")
    
    genai.configure(api_key=api_key)
    
    def search_web(query: str) -> str:
        """
        Ferramenta de busca na internet para encontrar notícias precisas sobre onde, que dia e que horas assistir a um jogo de futebol.
        Exemplo de query: 'jogo do flamengo hoje onde assistir canal'
        """
        logger.info(f"Gemini acionou busca via Tavily para: {query}")
        try:
            tavily_key = os.getenv("TAVILY_API_KEY")
            if not tavily_key or tavily_key == "COLE_SUA_CHAVE_TAVILY_AQUI":
                return "Erro: Chave da API do Tavily não configurada."
            
            client = TavilyClient(api_key=tavily_key)
            # Busca focada em encontrar informações de transmissão de próximos jogos
            response = client.search(query=query + " próximos jogos horário e onde assistir transmissão", search_depth="basic", max_results=4)
            
            results = []
            for result in response.get("results", []):
                title = result.get("title", "")
                content = result.get("content", "")
                results.append(f"Título: {title}\nResumo da Notícia: {content}")
                
            if not results:
                return "Nenhum resultado encontrado na web."
            return "\n\n".join(results)
        except Exception as e:
            logger.error(f"Erro na busca Tavily: {e}")
            return "Erro ao buscar na internet. Tente formular a resposta dizendo que não foi possível pesquisar as notícias de hoje."

    # Usando gemini-3.1-flash-lite
    hoje = datetime.datetime.now().strftime("%d/%m/%Y")
    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite",
        tools=[search_web],
        system_instruction=(
            f"Você é o bot 'Onde Vai Jogar' no Telegram.\n"
            f"A data de hoje é {hoje}. Use esta data como referência para identificar 'hoje', 'amanhã', etc.\n"
            f"REGRAS ESTRITAS DE RESPOSTA:\n"
            f"1. Seja extremamente direto. Sem rodeios ou introduções longas.\n"
            f"2. Informe APENAS: os times da partida, a data do jogo, o horário, e onde assistir (canal/streaming).\n"
            f"3. NÃO USE NENHUMA formatação Markdown (não use asteriscos **, não use hashtags #). Use apenas texto puro, quebras de linha e emojis.\n"
            f"4. Se o usuário pedir o 'próximo jogo' e houver um jogo HOJE, informe os dados do jogo de HOJE e também do PRÓXIMO jogo.\n"
            f"5. Use SEMPRE a ferramenta (search_web) para ter dados exatos. Nunca adivinhe."
        )
    )
    return model

def process_message(user_message: str) -> str:
    """Envia a mensagem para o Gemini (com função de busca automática) e retorna a resposta."""
    try:
        model = get_model()
        # Inicia um chat com enable_automatic_function_calling=True
        # Isso faz o Gemini executar a função search_web por conta própria e formular a resposta
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(user_message)
        return response.text
    except ValueError as ve:
        logger.error(f"Erro de Validação: {ve}")
        return "⚠️ Ops! A chave de API do Gemini ainda não foi configurada no arquivo `.env`."
    except Exception as e:
        logger.error(f"Erro ao processar mensagem com Gemini: {e}")
        return "Desculpe, tive um problema ao tentar processar sua mensagem ou realizar a busca no momento. Tente novamente mais tarde."
