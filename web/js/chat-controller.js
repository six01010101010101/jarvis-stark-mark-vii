/**
 * J.A.R.V.I.S. Mark VII // Chat & Voice Interaction Controller
 */

export class ChatController {
  constructor(apiClient, hologram, visualizer) {
    this.api = apiClient;
    this.hologram = hologram;
    this.visualizer = visualizer;
    this.historyElem = document.getElementById("chat-history");
    this.inputElem = document.getElementById("chat-input");
    this.sendBtn = document.getElementById("btn-send");
    this.micBtn = document.getElementById("btn-mic");
    this.stopBtn = document.getElementById("btn-stop");
    this.dialogueBadge = document.getElementById("active-dialogue-badge");
    this.dialogueCountdown = document.getElementById("dialogue-countdown");
    this.dialogueTimer = null;
    this.isListening = false;
    this.initEvents();
  }

  initEvents() {
    if (this.sendBtn) this.sendBtn.addEventListener("click", () => this.handleSend());
    if (this.inputElem) {
      this.inputElem.addEventListener("keypress", (e) => {
        if (e.key === "Enter") this.handleSend();
      });
    }
    if (this.micBtn) this.micBtn.addEventListener("click", () => this.toggleVoiceInput());
    if (this.stopBtn) this.stopBtn.addEventListener("click", () => this.handleStop());

    // Quick chips
    document.querySelectorAll(".chip-btn").forEach((chip) => {
      chip.addEventListener("click", () => {
        if (this.inputElem) {
          this.inputElem.value = chip.dataset.query || chip.textContent;
          this.handleSend();
        }
      });
    });
  }

  async handleSend() {
    const text = this.inputElem.value.trim();
    if (!text) return;
    this.inputElem.value = "";
    this.appendMessage("user", text);

    this.setInteractionState(true);
    const res = await this.api.sendChatMessage(text);
    this.setInteractionState(false);

    if (res && res.reply) {
      this.appendMessage("assistant", res.reply);
      this.speakText(res.reply);

      const normText = text.toLowerCase();
      const normReply = res.reply.toLowerCase();
      if (normText.includes("ajude") || normText.includes("ajuda") || normReply.includes("posso te ajudar, chefe")) {
        this.startActiveDialogueCountdown(15);
      } else if (normText.includes("piada") || normText.startsWith("abra") || normText.startsWith("feche") || normText.includes("alt tab")) {
        this.stopActiveDialogueCountdown();
      }
    }
  }

  startActiveDialogueCountdown(seconds = 15) {
    this.stopActiveDialogueCountdown();
    if (!this.dialogueBadge || !this.dialogueCountdown) return;
    this.dialogueBadge.style.display = "inline-flex";
    let rem = seconds;
    this.dialogueCountdown.textContent = `${rem}s`;

    this.dialogueTimer = setInterval(() => {
      rem -= 1;
      if (rem <= 0) {
        this.stopActiveDialogueCountdown();
      } else {
        this.dialogueCountdown.textContent = `${rem}s`;
      }
    }, 1000);
  }

  stopActiveDialogueCountdown() {
    if (this.dialogueTimer) {
      clearInterval(this.dialogueTimer);
      this.dialogueTimer = null;
    }
    if (this.dialogueBadge) {
      this.dialogueBadge.style.display = "none";
    }
  }

  handleStop() {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    this.stopActiveDialogueCountdown();
    this.setInteractionState(false);
    this.appendMessage("assistant", "Às suas ordens, senhor. Fala silenciada.");
  }

  appendMessage(role, text) {
    if (!this.historyElem) return;
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;
    const time = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    const sender = role === "user" ? "VOCÊ" : "J.A.R.V.I.S.";
    bubble.innerHTML = `<strong>[${time}] ${sender}:</strong><br>${this.escapeHtml(text)}`;
    this.historyElem.appendChild(bubble);
    this.historyElem.scrollTop = this.historyElem.scrollHeight;
  }

  setInteractionState(active) {
    if (this.hologram) this.hologram.setSpeaking(active);
    if (this.visualizer) this.visualizer.setActive(active);
  }

  speakText(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const clean = text.replace(/[*#`_]/g, "");
    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.lang = "pt-BR";
    utterance.rate = 1.05;
    utterance.onstart = () => this.setInteractionState(true);
    utterance.onend = () => this.setInteractionState(false);
    utterance.onerror = () => this.setInteractionState(false);
    window.speechSynthesis.speak(utterance);
  }

  toggleVoiceInput() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      alert("Reconhecimento de voz do navegador não suportado neste ambiente.");
      return;
    }
    if (this.isListening) return;

    const rec = new SpeechRec();
    rec.lang = "pt-BR";
    rec.onstart = () => {
      this.isListening = true;
      if (this.micBtn) this.micBtn.style.borderColor = "var(--hud-green)";
    };
    rec.onresult = (evt) => {
      const transcript = evt.results[0][0].transcript;
      if (this.inputElem) this.inputElem.value = transcript;
      this.handleSend();
    };
    rec.onend = () => {
      this.isListening = false;
      if (this.micBtn) this.micBtn.style.borderColor = "var(--hud-cyan-dim)";
    };
    rec.start();
  }

  escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}
