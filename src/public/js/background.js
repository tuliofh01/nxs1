const canvas = document.getElementById("bg");
const ctx = canvas.getContext("2d");

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
resize();
window.addEventListener("resize", resize);

// unique seed per visit
const seed = Math.random() * 999999;

function draw(t) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (let i = 0; i < 140; i++) {
    const x =
      (Math.sin(seed + i * 13.37) * 0.5 + 0.5) * canvas.width;
    const y =
      (Math.cos(seed + i + t * 0.0007) * 0.5 + 0.5) *
      canvas.height;

    ctx.fillStyle = "rgba(0,255,120,0.18)";
    ctx.fillRect(x, y, 2, 2);
  }

  requestAnimationFrame(draw);
}

requestAnimationFrame(draw);
