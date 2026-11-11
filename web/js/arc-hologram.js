/**
 * J.A.R.V.I.S. Mark VII // 3D Arc Reactor & Holographic Mask Canvas
 */

export class ArcHologram {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.angle = 0;
    this.pulse = 0;
    this.isSpeaking = false;
    this.resize();
    window.addEventListener("resize", () => this.resize());
    this.animate();
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const size = Math.min(rect.width, 320);
    this.canvas.width = size;
    this.canvas.height = size;
  }

  setSpeaking(speaking) {
    this.isSpeaking = speaking;
  }

  animate() {
    this.render();
    const speed = this.isSpeaking ? 0.045 : 0.018;
    this.angle += speed;
    this.pulse += this.isSpeaking ? 0.12 : 0.05;
    requestAnimationFrame(() => this.animate());
  }

  render() {
    const { ctx, canvas } = this;
    if (!ctx || !canvas) return;
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;

    ctx.clearRect(0, 0, w, h);

    const glowColor = this.isSpeaking ? "#00FF88" : "#00F0FF";
    const dimColor = this.isSpeaking ? "rgba(0, 255, 136, 0.25)" : "rgba(0, 240, 255, 0.25)";
    const pulseFactor = Math.sin(this.pulse) * (this.isSpeaking ? 8 : 3);

    // 1. Anel externo com ticks tecnológicos
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(this.angle);

    ctx.beginPath();
    ctx.arc(0, 0, 110 + pulseFactor * 0.3, 0, Math.PI * 2);
    ctx.strokeStyle = dimColor;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    for (let i = 0; i < 36; i++) {
      const a = (i * Math.PI) / 18;
      const r1 = 104;
      const r2 = i % 3 === 0 ? 116 : 108;
      ctx.beginPath();
      ctx.moveTo(Math.cos(a) * r1, Math.sin(a) * r1);
      ctx.lineTo(Math.cos(a) * r2, Math.sin(a) * r2);
      ctx.strokeStyle = i % 3 === 0 ? glowColor : dimColor;
      ctx.lineWidth = i % 3 === 0 ? 2 : 1;
      ctx.stroke();
    }
    ctx.restore();

    // 2. Anel intermediário contra-rotativo
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(-this.angle * 1.4);

    ctx.beginPath();
    ctx.arc(0, 0, 80, 0, Math.PI * 2);
    ctx.strokeStyle = glowColor;
    ctx.lineWidth = 2;
    ctx.shadowColor = glowColor;
    ctx.shadowBlur = 12;
    ctx.stroke();

    // 3 arcos segmentados
    for (let j = 0; j < 3; j++) {
      const startAngle = (j * 2 * Math.PI) / 3;
      ctx.beginPath();
      ctx.arc(0, 0, 88, startAngle, startAngle + Math.PI / 2.5);
      ctx.strokeStyle = glowColor;
      ctx.lineWidth = 3;
      ctx.stroke();
    }
    ctx.restore();

    // 3. Núcleo do Reator Arc Central
    ctx.save();
    ctx.translate(cx, cy);
    ctx.beginPath();
    const coreR = 36 + pulseFactor;
    ctx.arc(0, 0, coreR, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(0, 119, 182, 0.35)";
    ctx.fill();
    ctx.strokeStyle = glowColor;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = glowColor;
    ctx.shadowBlur = 18;
    ctx.stroke();

    // Triângulo central do Reator
    ctx.rotate(this.angle * 0.8);
    ctx.beginPath();
    for (let t = 0; t < 3; t++) {
      const ta = (t * 2 * Math.PI) / 3 - Math.PI / 2;
      const tr = 22;
      const x = Math.cos(ta) * tr;
      const y = Math.sin(ta) * tr;
      if (t === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.restore();
  }
}
