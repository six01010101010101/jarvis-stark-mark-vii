"""Personalidade e saudações cinematográficas do Homem de Ferro / Tony Stark."""

from __future__ import annotations

WAKE_PROMPT = "Sim, senhor, o que você gostaria de fazer?"

WAKE_RESPONSES = (
    "Sim, senhor, o que você gostaria de fazer?",
    "Sim, senhor, o que você gostaria?",
    "Pois não, senhor, o que você gostaria de fazer?",
    "Às suas ordens, senhor. O que gostaria que eu fizesse?",
)

TONY_STARK_GREETINGS = (
    "{greeting}, senhor {user}. Como está sendo o seu dia? Todos os sistemas calibrados. O que gostaria de fazer agora?",
    "{greeting}, senhor {user}. Os reatores estão a 100%. Sistemas operacionais prontos. O que tem em mente, senhor?",
    "{greeting}, senhor {user}. Diagnósticos concluídos e sensores ativos. Às suas ordens para executar qualquer tarefa.",
    "{greeting}, senhor {user}. Protocolos sincronizados. Estou à sua total disposição. O que deseja que eu execute hoje?",
)


def greeting_for(hour: int) -> str:
    """Saudação horária: 04-11 Bom dia, 12-17 Boa tarde, 18-03 Boa noite."""
    return "Bom dia" if 4 <= hour < 12 else ("Boa tarde" if 12 <= hour < 18 else "Boa noite")
