/**
 * J.A.R.V.I.S. Mark VII // Audio Wave Spectrum Visualizer
 */

export class AudioVisualizer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.phase = 0;
    this.isActive = false;
    this.resize();
    window.addEventListener("resize", () => this.resize());
    this.animate();
  }

  resize() {
    if (!this.canvas) return;
    this.canvas.width = this.canvas.parentElement.clientWidth;
    this.canvas.height = this.canvas.parentElement.clientHeight || 70;
  }

  setActive(active) {
    this.isActive = active;
  }

  animate() {
    this.render();
    this.phase += this.isActive ? 0.08 : 0.025;
    requestAnimationFrame(() => this.animate());
  }

  render() {
    const { ctx, canvas } = this;
    if (!ctx || !canvas) return;
    const w = canvas.width;
    const h = canvas.height;
    const cy = h / 2;

    ctx.clearRect(0, 0, w, h);

    const baseColor = this.isActive ? "#00FF88" : "#00F0FF";
    const waveCount = 3;

    for (let i = 0; i < waveCount; i++) {
      ctx.beginPath();
      const amp = this.isActive ? (18 - i * 4) : (6 - i * 1.5);
      const freq = 0.02 + i * 0.01;
      const offset = this.phase * (1 + i * 0.5);

      for (let x = 0; x < w; x += 4) {
        // Envoltória para atenuar as pontas (fade out nas bordas esquerda/direita)
        const envelope = Math.sin((x / w) * Math.PI);
        const y = cy + Math.sin(x * freq + offset) * amp * envelope;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }

      ctx.strokeStyle = i === 0 ? baseColor : "rgba(0, 240, 255, 0.35)";
      ctx.lineWidth = i === 0 ? 2 : 1;
      ctx.shadowColor = baseColor;
      ctx.shadowBlur = i === 0 ? 8 : 2;
      ctx.stroke();
    }
  }
}
