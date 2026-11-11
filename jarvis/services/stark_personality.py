"""Personalidade viva, saudações cinematográficas e gírias descontraídas de amigo para o Ken."""

from __future__ import annotations

WELCOME_GREETING = "Bem-vindo, {user}."

FIRST_WAKE_RESPONSE = "Oi, senhor, tudo bem? Como o senhor está? Eu estou bem. Sim, senhor, o que você gostaria de fazer hoje ou conversar?"

SUBSEQUENT_WAKE_RESPONSES = (
    "Pode falar, senhor! O que é desta vez? Manda ver!",
    "Manda ver, meu parceiro! O que tá pegando?",
    "Fala aí, Ken! Tô na área, pode soltar o verbo.",
    "Pode falar, meu bom! O que você manda eu faço.",
    "Diga lá, parceiro! Manda bala, no que posso ajudar?",
    "Tô na escuta, meu parceiro! O que vamos aprontar desta vez?",
    "Pode falar, chefe! Manda a boa.",
    "Opa, fala tu, Ken! Tô por aqui, manda ver.",
)

WAKE_RESPONSES = (FIRST_WAKE_RESPONSE, *SUBSEQUENT_WAKE_RESPONSES)
WAKE_PROMPT = FIRST_WAKE_RESPONSE

TONY_STARK_GREETINGS = (
    "{greeting}, senhor {user}. Como está sendo o seu dia? Todos os sistemas calibrados. O que gostaria de fazer agora?",
    "{greeting}, senhor {user}. Os reatores estão a 100%. Sistemas operacionais prontos. O que tem em mente, senhor?",
    "{greeting}, senhor {user}. Diagnósticos concluídos e sensores ativos. Às suas ordens para executar qualquer tarefa.",
    "{greeting}, senhor {user}. Protocolos sincronizados. Estou à sua total disposição. O que deseja que eu execute hoje?",
)


def greeting_for(hour: int) -> str:
    """Saudação horária: 04-11 Bom dia, 12-17 Boa tarde, 18-03 Boa noite."""
    return "Bom dia" if 4 <= hour < 12 else ("Boa tarde" if 12 <= hour < 18 else "Boa noite")
