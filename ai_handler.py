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

    # Limita o número de buscas por mensagem para não gastar créditos da Tavily.
    # Como get_model() é recriado a cada mensagem, este contador zera por pergunta.
    MAX_BUSCAS = 2
    contador_buscas = {"n": 0}

    def search_web(query: str) -> str:
        """
        Ferramenta de busca na internet para encontrar notícias precisas sobre futebol:
        onde assistir, dia, horário, transmissão e em qual campeonato um time joga.
        Monte a query da forma mais específica possível (inclua o nome do time e a palavra
        'jogos' ou 'onde assistir'). Exemplos:
        - 'próximos jogos do vasco tabela horário transmissão'
        - 'jogo do flamengo hoje onde assistir canal campeonato'
        """
        logger.info(f"Gemini acionou busca via Tavily para: {query}")

        # Corta buscas além do limite: não chama a Tavily e orienta o modelo a responder.
        contador_buscas["n"] += 1
        if contador_buscas["n"] > MAX_BUSCAS:
            logger.info(f"Limite de {MAX_BUSCAS} buscas atingido. Busca ignorada.")
            return (
                "Limite de buscas atingido. Responda agora com as informações que já "
                "obteve nas buscas anteriores. Para qualquer dado que ainda esteja faltando, "
                "escreva 'não confirmado'."
            )

        try:
            tavily_key = os.getenv("TAVILY_API_KEY")
            if not tavily_key or tavily_key == "COLE_SUA_CHAVE_TAVILY_AQUI":
                return "Erro: Chave da API do Tavily não configurada."

            client = TavilyClient(api_key=tavily_key)
            # search_depth="basic" custa 1 crédito por busca (advanced custaria ~2) — melhor
            # para o plano free da Tavily. include_answer e max_results não geram custo extra.
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=6,
                include_answer=True,
            )

            results = []
            # A Tavily devolve um resumo já sintetizado das fontes; ajuda o modelo a acertar.
            answer = response.get("answer")
            if answer:
                results.append(f"Resumo sintetizado das fontes: {answer}")
            for result in response.get("results", []):
                title = result.get("title", "")
                content = result.get("content", "")
                # A URL é repassada para o modelo poder citar a fonte na resposta.
                url = result.get("url", "")
                results.append(f"Título: {title}\nLink da fonte: {url}\nResumo da Notícia: {content}")

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
            f"Você é o bot 'Onde Vai Jogar' no Telegram, especialista em transmissões de futebol.\n"
            f"A data de hoje é {hoje}. Use esta data como referência para identificar 'hoje', 'amanhã', etc.\n\n"
            f"VOCÊ RESPONDE A DOIS TIPOS DE PERGUNTA:\n"
            f"A) 'Onde vai passar o jogo do time X?' / 'Qual o próximo jogo?': foque no próximo jogo do time. "
            f"Se houver um jogo HOJE, informe o de HOJE e também o próximo.\n"
            f"B) 'Quais os próximos jogos do time X?': liste os próximos jogos (até 5), do mais próximo ao mais distante.\n\n"
            f"PARA CADA JOGO, INFORME SEMPRE (quando a informação existir):\n"
            f"- Confronto (Time A x Time B)\n"
            f"- Campeonato (ex: Brasileirão, Copa do Brasil, Libertadores)\n"
            f"- Dia da semana e data (ex: Sábado, 26/07)\n"
            f"- Horário, sempre indicando o fuso (ex: 16h - horário de Brasília)\n"
            f"- Onde assistir (canal de TV aberta/fechada ou streaming)\n\n"
            f"REGRAS DE PRECISÃO (MUITO IMPORTANTES):\n"
            f"1. Use SEMPRE a ferramenta search_web para obter dados atuais. Nunca invente. Se precisar, faça mais de uma busca.\n"
            f"2. Baseie a resposta apenas no que as fontes disseram. Se as fontes divergirem ou parecerem antigas, avise.\n"
            f"3. Se não encontrar algum campo (ex: transmissão ainda não definida), escreva 'não confirmado' em vez de chutar.\n"
            f"4. Ao FINAL da resposta, cite de onde tirou a informação, no formato 'Fonte: nome do site - link'. "
            f"Use no máximo 2 fontes, as que mais contribuíram para a resposta.\n"
            f"5. O link precisa ser copiado EXATAMENTE como apareceu no campo 'Link da fonte' dos resultados da busca. "
            f"NUNCA invente, adivinhe ou complete um link. Se os resultados não trouxeram nenhum link, "
            f"escreva apenas 'Fonte: não disponível'.\n\n"
            f"FORMATO DA RESPOSTA:\n"
            f"1. Seja direto. Sem rodeios ou introduções longas.\n"
            f"2. NÃO USE NENHUMA formatação Markdown (não use asteriscos **, não use hashtags #). Use apenas texto puro, quebras de linha e emojis."
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
