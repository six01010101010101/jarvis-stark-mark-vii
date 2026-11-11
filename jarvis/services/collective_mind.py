"""Motor de Mente Coletiva do J.A.R.V.I.S. Mark VII (Gemini + Raciocínio Profundo + Fatos)."""

from __future__ import annotations

import logging
import os
import re

from jarvis.repositories.memory_repository import MemoryRepository
from jarvis.services.collective_prompts import JARVIS_COLLECTIVE_MIND_PROMPT
from jarvis.services.semantic_wake_analyzer import SemanticWakeAnalyzer
from jarvis.text_utils import normalize

logger = logging.getLogger(__name__)

STARK_SELF_EXPLANATION = (
    "Eu sou o J.A.R.V.I.S., sigla para Just A Rather Very Intelligent System, operando na arquitetura Mark Sete. "
    "Assim como a inteligência artificial criada por Tony Stark no Homem de Ferro, fui projetado para gerenciar "
    "seus sistemas, integrar sua GPU RTX 4060, Máquina Virtual e Banco de Dados Central em tempo real, atuando como "
    "seu parceiro e conselheiro estratégico. Quer que eu apresente os dados de telemetria agora ou prefere que "
    "discutamos alguma ideia em que você está trabalhando?"
)


class JarvisCollectiveMind:
    """Motor cognitivo de alta densidade que sintetiza múltiplos ângulos analíticos e fatos do usuário."""

    def __init__(self, repo: MemoryRepository, gemini_service: object | None = None) -> None:
        self.repo = repo
        self._gemini = gemini_service

    def think_and_reply(self, user_text: str, in_patience_window: bool = False, lang: str = "pt") -> tuple[str, str]:
        """Processa a oração, distingue vocativo de tema e retorna (resposta_inteligente, modo_intencao)."""
        analysis = SemanticWakeAnalyzer.analyze_utterance(user_text, in_patience_window=in_patience_window)
        if not analysis["should_process"]:
            return "", "IGNORE"

        if analysis["intent_mode"] == "PURE_WAKE":
            greetings = {
                "pt": "Estou aqui, senhor. Sobre o que vamos raciocinar agora?",
                "en": "Online and listening, sir. What's on your mind?",
                "es": "Aquí estoy, señor. ¿En qué trabajamos ahora?",
            }
            return greetings.get(lang.split("-")[0], greetings["pt"]), "PURE_WAKE"

        query = str(analysis["clean_query"])
        q_norm = normalize(query)

        # Resposta de autoconsciência imediata se for sobre a própria identidade
        if any(w in q_norm for w in ("quem e voce", "quem e o jarvis", "o que e o jarvis", "o que seria o jarvis", "como voce funciona")) or (
            "jarvis" in q_norm and any(w in q_norm for w in ("o que", "quem", "seria", "como funciona", "explica", "o que e", "quem e"))
        ):
            self.repo.save_episodic_turn(query, STARK_SELF_EXPLANATION, intent_type="DEEP_CONVERSATION", lang=lang)
            return STARK_SELF_EXPLANATION, "DEEP_CONVERSATION"

        # Constrói o contexto com fatos aprendidos + histórico recente da conversa
        learned_facts = self.repo.get_learned_facts(limit=12)
        facts_block = "\n".join(f"- {f}" for f in learned_facts) if learned_facts else "Nenhum fato adicional."
        recent_history = self.repo.get_recent_episodic_context(limit=10)
        history_str = "\n".join(f"{'Usuário' if h['role'] == 'user' else 'J.A.R.V.I.S.'}: {h['content']}" for h in recent_history)

        full_prompt = (
            f"{JARVIS_COLLECTIVE_MIND_PROMPT}\n\n"
            f"[FATOS NA MEMÓRIA CENTRAL DO USUÁRIO]:\n{facts_block}\n\n"
            f"[HISTÓRICO RECENTE DA CONVERSA]:\n{history_str}\n\n"
            f"[IDIOMA]: Responda fluentemente no idioma '{lang}'.\n"
            f"[PERGUNTA DO USUÁRIO]: {query}\n\n"
            f"Instrução: Responda de forma profunda, brilhante e natural, finalizando com uma pergunta relevante."
        )

        reply = self._query_llm_or_fallback(query, full_prompt)
        self.repo.save_episodic_turn_async(query, reply, intent_type="DEEP_CONVERSATION", lang=lang)
        return reply, "DEEP_CONVERSATION"

    def _query_llm_or_fallback(self, query: str, full_prompt: str) -> str:
        if self._gemini and hasattr(self._gemini, "ask"):
            try:
                res = self._gemini.ask(full_prompt)
                clean = re.sub(r"[*#`]+", "", res).strip()
                if clean:
                    return clean
            except Exception as exc:
                logger.debug("Falha em consulta LLM direta na Mente Coletiva: %s", exc)

        try:
            from google import genai
            client = genai.Client()
            model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            resp = client.models.generate_content(model=model, contents=full_prompt)
            if resp and resp.text:
                return re.sub(r"[*#`]+", "", resp.text).strip()
        except Exception:
            pass

        return (
            f"Analisei sua reflexão sobre '{query}', senhor. Nossos módulos e telemetria estão 100% online. "
            f"Gostaria que eu aprofundasse esse assunto pelo viés técnico ou prefere traçarmos uma estratégia prática?"
        )
