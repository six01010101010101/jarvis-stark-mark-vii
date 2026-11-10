"""Protocolos e Easter Eggs clássicos do J.A.R.V.I.S. dos filmes do Homem de Ferro."""

from __future__ import annotations

from pathlib import Path
from jarvis.commands.registry import Command, CommandContext, Outcome

BOOT_JARVIS_MP3 = Path(r"c:\Users\s6x12\Downloads\InteligenciaArtificial-IA-main\InteligenciaArtificial-IA-main\Jarvis_1.0\BootJarvis.MP3")


def _house_party(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Protocolo Festa de Arromba acionado, senhor Ken! Todas as armaduras automatizadas "
        "e subsistemas do computador foram colocados em prontidão defensiva."
    )
    return Outcome.CONTINUE


def _flight_mode(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Propulsores e compensadores inerciais calibrados a 100%, senhor Ken. "
        "Recomendo manter a postura antes de ultrapassarmos a barreira do som."
    )
    return Outcome.CONTINUE


def _arc_reactor(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Núcleo do Reator Arc estabilizado e operando a 3 gigajoules por segundo, senhor Ken. "
        "Campos magnéticos e dissipação térmica plenamente funcionais."
    )
    return Outcome.CONTINUE


def _who_is_boss(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "O senhor Tony Stark concebeu meus circuitos originais, mas minhas diretrizes primárias "
        "estão dedicadas com total fidelidade ao comando do senhor Ken."
    )
    return Outcome.CONTINUE


def _dum_e(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Acionei o robô DUM-E para organizar a bancada da oficina, senhor Ken. "
        "Torçamos para que ele não tente usar o extintor de incêndio na placa-mãe novamente."
    )
    return Outcome.CONTINUE


def _run_before_walk(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Entendido, senhor Ken. Como diria o senhor Stark: às vezes você tem que correr "
        "antes de aprender a andar. Limitadores desativados. Em 3, 2, 1... Potência total."
    )
    return Outcome.CONTINUE


def _virtual_tour(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(
        "Importando preferências e calibrando o ambiente virtual, senhor Ken. "
        "Faça uma checagem dos controles. Estamos conectados e prontos."
    )
    return Outcome.CONTINUE


def _movie_audio(ctx: CommandContext, _utterance: str) -> Outcome:
    if BOOT_JARVIS_MP3.exists():
        ctx.reply("Transmitindo gravação do áudio clássico da armadura Mark, senhor Ken.")
        from jarvis.services.neural_speaker import _play_mp3_native
        _play_mp3_native(BOOT_JARVIS_MP3)
    else:
        ctx.reply("Ao seu dispor, senhor Ken. Áudio clássico executado nos subsistemas de fala.")
    return Outcome.CONTINUE


def marvel_commands() -> list[Command]:
    """Retorna comandos táticos e falas clássicas dos filmes do Homem de Ferro."""
    return [
        Command("house_party", ("protocolo festa de arromba", "festa de arromba", "house party"), _house_party),
        Command("flight_mode", ("protocolo de voo", "ligar propulsores", "iniciar voo", "preparar para voar"), _flight_mode),
        Command("arc_reactor", ("iniciar reator arc", "potencia maxima", "reator arc", "status do reator"), _arc_reactor),
        Command("who_is_boss", ("quem e o homem de ferro", "quem manda em voce", "quem e seu criador", "sua origem"), _who_is_boss),
        Command("dum_e", ("limpar oficina", "limpar a oficina", "chamar dumm e", "robo dumm e"), _dum_e),
        Command("run_walk", ("correr antes de andar", "corra antes de andar", "as vezes voce tem que correr"), _run_before_walk),
        Command("virtual_tour", ("passeio virtual", "iniciar passeio virtual", "calibrar ambiente"), _virtual_tour),
        Command("movie_boot", ("audio do filme", "tocar boot", "audio do homem de ferro", "boot jarvis"), _movie_audio),
    ]
