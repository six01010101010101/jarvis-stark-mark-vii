"""Serviço de inteligência de mundo real: cálculo matemático, tempo, clima e fatos."""

from __future__ import annotations

import ast
import operator
import re
from datetime import datetime
from typing import Callable

from jarvis.contracts import AnswerProvider

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}

DAYS_PT = (
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
)
MONTHS_PT = (
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def _eval_ast(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return SAFE_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPERATORS:
        return SAFE_OPERATORS[type(node.op)](_eval_ast(node.operand))
    raise ValueError("Operação matemática não suportada")


class WorldIntelligence:
    """Resolve consultas factuais de mundo, operações aritméticas e informações de tempo."""

    def __init__(
        self,
        answers: AnswerProvider,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._answers = answers
        self._clock = clock

    def evaluate_math(self, utterance: str) -> str | None:
        """Extrai e calcula expressões matemáticas seguras via AST."""
        cleaned = utterance.lower()
        cleaned = re.sub(r"quanto\s+[ée]\s*|calcule\s*|qual\s+[ée]\s*o\s*resultado\s*de\s*", "", cleaned)
        cleaned = cleaned.replace(" vezes ", " * ").replace(" x ", " * ")
        cleaned = cleaned.replace(" dividido por ", " / ").replace(" sobre ", " / ")
        cleaned = cleaned.replace(" mais ", " + ").replace(" menos ", " - ")
        cleaned = cleaned.replace(" elevado a ", " ** ").replace("^", " ** ")

        match = re.search(r"[-+]?\s*\(?\s*\d+(?:[\.,]\d+)?\s*(?:[\+\-\*\/\%]\s*\(?\s*[-+]?\d+(?:[\.,]\d+)?\s*\)?)+", cleaned)
        if not match:
            return None

        expr = match.group(0).replace(",", ".").strip()
        try:
            tree = ast.parse(expr, mode="eval")
            res = _eval_ast(tree.body)
            formatted = f"{res:.2f}".rstrip("0").rstrip(".") if isinstance(res, float) else str(res)
            return f"O resultado do cálculo é {formatted}, senhor."
        except Exception:  # noqa: BLE001
            return None

    def get_time_report(self) -> str:
        """Informa as horas exatas no fuso horário do usuário."""
        now = self._clock()
        return f"Agora são exatamente {now.strftime('%H:%M')}, senhor."

    def get_date_report(self) -> str:
        """Informa a data completa e o dia da semana."""
        now = self._clock()
        weekday = DAYS_PT[now.weekday()]
        month = MONTHS_PT[now.month]
        return f"Hoje é {weekday}, dia {now.day} de {month} de {now.year}, senhor."

    def answer_direct(self, query: str) -> str:
        """Envia pergunta objetiva para o Gemini com instrução de resposta direta e sem rodeios."""
        prompt = (
            f"Você é o J.A.R.V.I.S. Responda à pergunta do senhor de forma 100% direta, factual, precisa "
            f"e objetiva, sem rodeios ou distrações. Pergunta: {query}"
        )
        return self._answers.ask(prompt)
