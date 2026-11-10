"""Motor cognitivo: gera mapas mentais em Mermaid, notas adesivas, flashcards e roteiros."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from jarvis.contracts import AnswerProvider, CognitiveService
from jarvis.repositories.artifact_repository import ArtifactRepository

logger = logging.getLogger(__name__)

DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "jarvis_artifacts"


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    return re.sub(r"[-\s]+", "_", cleaned) or "artefato"


class CognitiveEngine(CognitiveService):
    """Executa os arquétipos cognitivos de aprendizagem e persiste como artefatos."""

    def __init__(
        self,
        answers: AnswerProvider,
        artifacts: ArtifactRepository,
        artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
    ) -> None:
        self._answers = answers
        self._artifacts = artifacts
        self._artifacts_dir = artifacts_dir
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _generate_and_save(
        self,
        artifact_type: str,
        title: str,
        prompt: str,
        format_type: str = "markdown",
    ) -> str:
        content = self._answers.ask(prompt)
        self._artifacts.save_artifact(artifact_type, title, content, format_type)
        try:
            filename = f"{_sanitize_filename(title)}_{artifact_type}.md"
            filepath = self._artifacts_dir / filename
            filepath.write_text(content, encoding="utf-8")
            logger.info("Artefato salvo no disco: %s", filepath)
        except OSError as exc:
            logger.warning("Falha ao salvar artefato no disco: %s", exc)
        return content

    def generate_mind_map(self, topic: str) -> str:
        prompt = (
            f"Crie um mapa mental sobre '{topic}'. Use: um conceito central, categorias principais, "
            f"subcategorias, palavras-chave e relações entre conceitos. Entregue primeiro em formato de "
            f"árvore Markdown e depois em código Mermaid válido com mindmap."
        )
        self._generate_and_save("mind_map", topic, prompt, format_type="mermaid")
        return f"Mapa mental sobre {topic} estruturado em código Mermaid e salvo com sucesso, senhor."

    def generate_sticky_notes(self, topic: str) -> str:
        prompt = (
            f"Organize o tema '{topic}' em notas adesivas. Separe nas seguintes categorias: "
            f"conceito principal, como funciona, exemplos, cuidados, erros comuns, dicas práticas e resumo. "
            f"Cada nota deve ter uma frase curta, clara e independente."
        )
        self._generate_and_save("sticky_notes", topic, prompt)
        return f"Notas adesivas sobre {topic} organizadas e arquivadas, senhor."

    def generate_visual_learning(self, topic: str) -> str:
        prompt = (
            f"Explique visualmente o tema '{topic}' em estilo infográfico educacional: 1. Definição simples; "
            f"2. Diagrama de relações conceituais; 3. Exemplo prático; 4. Sequência passo a passo; "
            f"5. Erros mais comuns; 6. Resumo final objetivo."
        )
        self._generate_and_save("visual_learning", topic, prompt)
        return f"Guia de aprendizagem visual sobre {topic} concluído, senhor."

    def explain_three_levels(self, topic: str) -> str:
        prompt = (
            f"Explique '{topic}' em três níveis: 1. Iniciante (linguagem simples e analogia); "
            f"2. Intermediário (conceitos técnicos e exemplo prático); 3. Avançado (detalhes, limitações "
            f"e boas práticas). Finalize comparando o que muda entre os níveis."
        )
        self._generate_and_save("three_levels", topic, prompt)
        return f"Explicação em três níveis sobre {topic} elaborada e salva, senhor."

    def generate_flashcards(self, topic: str) -> str:
        prompt = (
            f"Crie 15 flashcards de estudo sobre '{topic}' no formato Pergunta e Resposta. Distribua em: "
            f"6 básicos, 6 intermediários e 3 avançados. Respostas curtas, precisas e fáceis de revisar."
        )
        self._generate_and_save("flashcards", topic, prompt)
        return f"Conjunto de flashcards sobre {topic} gerado e salvo nos seus artefatos, senhor."

    def generate_quiz(self, topic: str) -> str:
        prompt = (
            f"Crie um quiz interativo com 5 perguntas sobre '{topic}'. Para cada questão forneça 4 alternativas, "
            f"indique o gabarito e uma breve justificativa educativa."
        )
        self._generate_and_save("quiz", topic, prompt)
        return f"Quiz interativo sobre {topic} preparado e registrado com sucesso, senhor."

    def generate_study_roadmap(self, topic: str, period: str = "4 semanas") -> str:
        prompt = (
            f"Crie um plano de estudos estruturado para dominar '{topic}' no período de {period}. "
            f"Organize semana a semana com: teoria essencial, prática aplicada, exercícios e projeto final."
        )
        self._generate_and_save("study_roadmap", topic, prompt)
        return f"Roteiro de estudos para {topic} planejado para {period}, senhor."
