"""Comandos de voz para controle e consulta do Proton VPN."""

from __future__ import annotations

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.proton_vpn import ProtonVPNManager

_vpn_manager = ProtonVPNManager()


def _connect_vpn_handler(ctx: CommandContext, _utterance: str) -> Outcome:
    if not _vpn_manager.is_installed():
        ctx.reply("O Proton VPN não foi localizado no diretório padrão da máquina, senhor.")
        return Outcome.CONTINUE

    # 1. Fala a confirmação primeiro (protocolo sequencial estrito)
    ctx.reply("Iniciando conexão segura com a rede internacional do Proton VPN, senhor.")
    # 2. Executa a abertura após a fala
    _vpn_manager.launch_client()
    return Outcome.CONTINUE


def _disconnect_vpn_handler(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply("Desativando conexão de rede privada VPN, senhor.")
    _vpn_manager.disconnect()
    return Outcome.CONTINUE


def _status_vpn_handler(ctx: CommandContext, _utterance: str) -> Outcome:
    is_tunnel_active = _vpn_manager.is_connected()
    info = _vpn_manager.get_public_ip_info()
    ip, country = info.get("ip", "desconhecido"), info.get("country", "desconhecido")
    tunnel_str = "Túnel ativo" if is_tunnel_active else "Túnel em espera"
    ctx.reply(f"Status da rede: {tunnel_str}. Seu IP público atual é {ip}, registrado no país {country}, senhor.")
    return Outcome.CONTINUE


def vpn_commands() -> tuple[Command, ...]:
    """Retorna os comandos de voz associados ao gerenciamento do Proton VPN."""
    return (
        Command(
            name="connect_vpn",
            triggers=("ativar vpn", "conectar vpn", "ligar vpn", "abrir vpn", "iniciar vpn", "conectar proton vpn"),
            handler=_connect_vpn_handler,
        ),
        Command(
            name="disconnect_vpn",
            triggers=("desativar vpn", "desconectar vpn", "desligar vpn", "fechar vpn", "parar vpn", "desconectar proton vpn"),
            handler=_disconnect_vpn_handler,
        ),
        Command(
            name="status_vpn",
            triggers=("status da vpn", "status vpn", "qual meu ip", "onde estou conectado", "qual pais vpn", "qual país vpn"),
            handler=_status_vpn_handler,
        ),
    )
