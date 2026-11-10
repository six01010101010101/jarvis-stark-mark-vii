"""Diagnóstico completo e integrado de voz (saída de áudio) e microfone (entrada de fala)."""

from __future__ import annotations

import time

from jarvis.speech.audio_stream import list_input_devices, pick_default_device_index
from jarvis.speech.listener import GoogleSpeechListener
from jarvis.speech.tts import build_speaker
from jarvis.text_utils import extract_wake_and_command


def run_full_diagnostic() -> None:
    print("=" * 65)
    print("   J.A.R.V.I.S. // DIAGNÓSTICO INTEGRADO DE ENTRADA E SAÍDA")
    print("=" * 65)

    # 1. Teste de Síntese de Voz Limpa (Saída de Áudio)
    print("\n[ETAPA 1/2] Testando sintetizador neural com voz limpa (Edge-TTS Antonio)...")
    speaker = build_speaker(on_start=lambda: None, on_end=lambda: None)
    test_phrase = "Sim, senhor Ken? Todos os meus sistemas de voz e áudio estão operacionais com voz limpa."
    print(f"Falando agora: \"{test_phrase}\"")
    try:
        speaker.say(test_phrase)
        print("  -> Saída de voz neural reproduzida com sucesso!")
    except Exception as exc:
        print(f"  -> [ERRO] Falha na saída de áudio: {exc}")

    time.sleep(1)

    # 2. Teste de Reconhecimento de Microfone (Entrada de Fala)
    print("\n" + "-" * 65)
    print("[ETAPA 2/2] Testando captação do microfone e detecção do nome 'Jarvis'...")
    devs = list_input_devices()
    chosen_idx = pick_default_device_index(devs)
    print(f"Dispositivo selecionado: [{chosen_idx}]")

    def show_vol(pct: float) -> None:
        bars = int(pct * 25)
        bar_str = "█" * bars + "░" * (25 - bars)
        print(f"\r  Nível de voz: [{bar_str}] {int(pct * 100)}%   ", end="", flush=True)

    listener = GoogleSpeechListener(
        language="pt-BR",
        device_index=chosen_idx,
        on_volume=show_vol,
    )

    print("\n>>> FALE 'JARVIS' NO SEU MICROFONE AGORA! <<<")
    try:
        for attempt in range(1, 4):
            print(f"\n[Tentativa {attempt}/3] Aguardando sua voz no microfone...")
            phrase = listener.listen()
            if phrase:
                print(f"\n=======================================================")
                print(f"  TRANSCRIÇÃO DO GOOGLE VIA TERMINAL: \"{phrase}\"")
                print(f"=======================================================")
                is_wake, inline = extract_wake_and_command(phrase, "jarvis")
                if is_wake:
                    print("\n>>> SUCESSO! Nome 'Jarvis' identificado pelo terminal! <<<")
                    speaker.say("Sim, senhor Ken? Identifiquei seu chamado perfeitamente.")
                    break
                else:
                    print(f"[INFO] Frase recebida: '{phrase}'. Diga 'Jarvis' para ativar.")
            else:
                print("[AVISO] Nenhuma fala captada. Fale mais próximo ao microfone.")
    finally:
        listener.close()

    print("\nDiagnóstico integrado concluído.")


if __name__ == "__main__":
    run_full_diagnostic()
