/**
 * J.A.R.V.I.S. Mark VII // Telemetry & System State Widget
 */

export class TelemetryWidget {
  constructor(apiClient) {
    this.api = apiClient;
    this.cpuElem = document.getElementById("metric-cpu");
    this.cpuBar = document.getElementById("bar-cpu");
    this.ramElem = document.getElementById("metric-ram");
    this.ramBar = document.getElementById("bar-ram");
    this.diskElem = document.getElementById("metric-disk");
    this.vpnElem = document.getElementById("vpn-status-tag");
    this.factsContainer = document.getElementById("learned-facts-list");
    this.initPolling();
  }

  initPolling() {
    this.update();
    setInterval(() => this.update(), 3000);
  }

  async update() {
    const data = await this.api.getTelemetry();
    if (data) {
      const cpu = Math.round(data.cpu_percent || 0);
      const ramUsed = Number(data.ram_used_gb || 0).toFixed(1);
      const ramFree = Number(data.ram_free_gb || 0).toFixed(1);
      const totalRam = (Number(data.ram_used_gb || 0) + Number(data.ram_free_gb || 0)) || 16;
      const ramPct = Math.round((Number(data.ram_used_gb || 0) / totalRam) * 100);
      const diskFree = Number(data.disk_free_gb || 0).toFixed(0);

      if (this.cpuElem) this.cpuElem.textContent = `${cpu}%`;
      if (this.cpuBar) this.cpuBar.style.width = `${Math.min(100, Math.max(5, cpu))}%`;

      if (this.ramElem) this.ramElem.textContent = `${ramUsed}GB / ${ramPct}%`;
      if (this.ramBar) this.ramBar.style.width = `${Math.min(100, Math.max(5, ramPct))}%`;

      if (this.diskElem) this.diskElem.textContent = `${diskFree} GB Livres`;
    }

    const mem = await this.api.getMemory();
    if (mem && mem.facts && this.factsContainer) {
      this.factsContainer.innerHTML = "";
      const facts = mem.facts.slice(0, 5);
      if (facts.length === 0) {
        this.factsContainer.innerHTML = "<div class='metric-header'>Nenhum fato gravado.</div>";
      } else {
        facts.forEach((fact) => {
          const item = document.createElement("div");
          item.className = "metric-card";
          item.style.fontSize = "0.78rem";
          item.style.marginBottom = "0.4rem";
          item.textContent = `• ${fact}`;
          this.factsContainer.appendChild(item);
        });
      }
    }
  }
}
