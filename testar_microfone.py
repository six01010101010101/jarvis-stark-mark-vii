"""Ferramenta interativa de diagnóstico de microfone, áudio e reconhecimento de voz."""

from __future__ import annotations

import io
import time
import wave
import winsound

import speech_recognition as sr

from jarvis.speech.audio_stream import compute_rms, list_input_devices, pick_default_device_index


def run_mic_test() -> None:
    print("=" * 65)
    print("      J.A.R.V.I.S. // DIAGNÓSTICO ACÚSTICO E TESTE DE MICROFONE")
    print("=" * 65)

    devices = list_input_devices()
    if not devices:
        print("[ERRO] Nenhum dispositivo de entrada encontrado no Windows!")
        return

    print("\n[DISPOSITIVOS DETECTADOS NO SEU WINDOWS]:")
    chosen_idx = pick_default_device_index(devices)
    for d in devices:
        marker = "-> [ATIVO]" if d.index == chosen_idx else "          "
        print(f" {marker} [{d.index}] {d.name} ({d.sample_rate}Hz, {d.channels} canais)")

    print("-" * 65)
    print(f"[TESTANDO AGORA]: Dispositivo [{chosen_idx}]")
    print("Fale 'JARVIS' claramente nos proximos 4 segundos...")
    print("Começando em:")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print("\n>>> PODE FALAR AGORA! (GRAVANDO 4 SEGUNDOS)... <<<\n")

    import pyaudio

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        input_device_index=chosen_idx,
        frames_per_buffer=1024,
    )

    frames: list[bytes] = []
    max_rms = 0
    start_time = time.time()

    while time.time() - start_time < 4.0:
        data = stream.read(1024, exception_on_overflow=False)
        frames.append(data)
        rms = compute_rms(data)
        if rms > max_rms:
            max_rms = rms
        pct = min(rms / 1000.0, 1.0)
        bars = int(pct * 30)
        bar_str = "█" * bars + "░" * (30 - bars)
        print(f"\r  Nível de captação: [{bar_str}] {int(pct * 100)}% (RMS: {rms})   ", end="", flush=True)

    stream.stop_stream()
    stream.close()
    p.terminate()

    print("\n\n[GRAVAÇÃO CONCLUÍDA!]")
    print(f"Pico de volume atingido: {max_rms} RMS")

    if max_rms < 80:
        print("\n[ALERTA]: O som captado foi quase ZERO (silêncio).")
        print("  - Verifique se o microfone está mutado no teclado/headset ou no Windows.")
        print("  - Ou tente selecionar outro dispositivo na lista acima.")
    else:
        print("[SUCESSO]: Áudio captado com boa amplitude!")

    # Reproduz o áudio gravado
    print("\n[REPRODUZINDO SUA VOZ]: Ouvindo o que o microfone gravou...")
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"".join(frames))
    wav_bytes = wav_io.getvalue()
    winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)

    # Teste de Transcrição Google
    print("\n[TESTE DE RECONHECIMENTO GOOGLE STT]: Enviando ao servidor...")
    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(b"".join(frames), 16000, 2)
    try:
        texto = recognizer.recognize_google(audio_data, language="pt-BR")
        print(f"\n=======================================================")
        print(f"  O GOOGLE RECONHECEU: \"{texto}\"")
        print(f"=======================================================")
        if any(w in texto.lower() for w in ("jarvis", "chaves", "chave", "javi", "davis")):
            print("\n>>> O NOME 'JARVIS' FOI IDENTIFICADO COM PERFEIÇÃO! <<<")
            print("Seu sistema está pronto para responder quando você falar!")
    except sr.UnknownValueError:
        print("\n[INFO]: O áudio foi captado, mas o Google não discerniu palavras com clareza.")
        print("Dica: Fale mais próximo ao microfone ou ajuste o ganho no Windows.")
    except Exception as exc:
        print(f"\n[ERRO DE CONEXÃO]: {exc}")

    print("\nDiagnóstico finalizado.")


if __name__ == "__main__":
    run_mic_test()
