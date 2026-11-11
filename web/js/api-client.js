/**
 * J.A.R.V.I.S. Mark VII // API Client
 * Comunicação assíncrona com o servidor REST (porta 8765).
 */

export class JarvisApiClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl || window.location.origin;
  }

  async getStatus() {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/status`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("[JarvisApiClient] Erro ao obter status:", err);
      return null;
    }
  }

  async getTelemetry() {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/telemetry`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("[JarvisApiClient] Erro ao obter telemetria:", err);
      return null;
    }
  }

  async getMemory() {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/memory`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("[JarvisApiClient] Erro ao obter memória:", err);
      return null;
    }
  }

  async sendChatMessage(message, lang = "pt") {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, lang }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error("[JarvisApiClient] Erro no chat:", err);
      return {
        reply: "Falha na conexão neural com o servidor Mark VII, senhor. Verifique o status da porta 8765.",
        intent_mode: "ERROR",
      };
    }
  }
}
