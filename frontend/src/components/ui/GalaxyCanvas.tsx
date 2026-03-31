'use client';
import { useEffect, useRef } from 'react';

export default function GalaxyCanvas() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const mobile = window.innerWidth < 768;
    const DPR = window.devicePixelRatio || 1;

    const resize = () => {
      canvas.width = window.innerWidth * DPR;
      canvas.height = window.innerHeight * DPR;
      canvas.style.width = window.innerWidth + 'px';
      canvas.style.height = window.innerHeight + 'px';
      ctx.scale(DPR, DPR);
    };
    resize();
    window.addEventListener('resize', resize);

    const COLORS = ['#FFFFFF', '#FFFFFF', '#FF7A3D', '#FF4D00', '#00E5CC', '#FFFFFF', '#00B5A0', '#FFB87A'];

    const starCount = mobile ? 80 : 160;
    interface Star {
      x: number; y: number; r: number; color: string;
      phase: number; speed: number; baseOp: number;
    }
    const stars: Star[] = Array.from({ length: starCount }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() * 1.2 + 0.3,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      phase: Math.random() * Math.PI * 2,
      speed: Math.random() * 0.6 + 0.3,
      baseOp: Math.random() * 0.5 + 0.2,
    }));

    const shootCount = mobile ? 3 : 6;
    interface Shoot {
      x: number; y: number; len: number; speed: number; color: string;
      progress: number; delay: number; timer: number; active: boolean;
    }
    const shoots: Shoot[] = Array.from({ length: shootCount }, (_, i) => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight * 0.4,
      len: Math.random() * 180 + 100,
      speed: Math.random() * 8 + 6,
      color: ['#FFFFFF', '#FF7A3D', '#00E5CC', '#FFD580'][i % 4],
      progress: Math.random(),
      delay: Math.random() * 8,
      timer: 0,
      active: false,
    }));

    const dustCount = mobile ? 30 : 70;
    interface Dust {
      x: number; y: number; r: number; color: string;
      vy: number; vx: number; life: number; lifeSpeed: number;
    }
    const DUST_COLORS = ['rgba(255,120,60,', 'rgba(0,229,204,', 'rgba(255,210,128,'];
    const dusts: Dust[] = Array.from({ length: dustCount }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() * 0.8 + 0.2,
      color: DUST_COLORS[Math.floor(Math.random() * DUST_COLORS.length)],
      vy: -(Math.random() * 0.3 + 0.05),
      vx: (Math.random() - 0.5) * 0.2,
      life: Math.random(),
      lifeSpeed: Math.random() * 0.002 + 0.001,
    }));

    let raf: number;
    let t = 0;

    const draw = () => {
      const W = window.innerWidth;
      const H = window.innerHeight;
      ctx.clearRect(0, 0, W, H);

      // Fond prune-noir
      ctx.fillStyle = '#06040E';
      ctx.fillRect(0, 0, W, H);

      // Nébuleuse orange (haut-gauche)
      const g1 = ctx.createRadialGradient(W * 0.2, H * 0.3, 0, W * 0.2, H * 0.3, W * 0.35);
      g1.addColorStop(0, 'rgba(255,77,0,0.06)');
      g1.addColorStop(1, 'transparent');
      ctx.fillStyle = g1;
      ctx.fillRect(0, 0, W, H);

      // Nébuleuse teal (droite)
      const g2 = ctx.createRadialGradient(W * 0.82, H * 0.55, 0, W * 0.82, H * 0.55, W * 0.28);
      g2.addColorStop(0, 'rgba(0,229,204,0.05)');
      g2.addColorStop(1, 'transparent');
      ctx.fillStyle = g2;
      ctx.fillRect(0, 0, W, H);

      // Nébuleuse ambre (bas-centre)
      const g3 = ctx.createRadialGradient(W * 0.5, H * 0.85, 0, W * 0.5, H * 0.85, W * 0.22);
      g3.addColorStop(0, 'rgba(255,160,80,0.04)');
      g3.addColorStop(1, 'transparent');
      ctx.fillStyle = g3;
      ctx.fillRect(0, 0, W, H);

      // Si reduced-motion, on s'arrête là (fond statique sans animations)
      if (reduced) {
        // Étoiles statiques sans scintillement
        for (const s of stars) {
          ctx.beginPath();
          ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
          ctx.globalAlpha = s.baseOp;
          ctx.fillStyle = s.color;
          ctx.fill();
          ctx.globalAlpha = 1;
        }
        raf = requestAnimationFrame(draw);
        return;
      }

      t += 0.01;

      // Étoiles scintillantes
      for (const s of stars) {
        const op = s.baseOp + Math.sin(t * s.speed + s.phase) * (s.baseOp * 0.8);
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.globalAlpha = Math.max(0, Math.min(1, op));
        ctx.fillStyle = s.color;
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      // Poussière cosmique (particules flottantes)
      for (const d of dusts) {
        d.life += d.lifeSpeed;
        if (d.life > 1) {
          d.life = 0;
          d.x = Math.random() * W;
          d.y = Math.random() * H;
        }
        d.x += d.vx;
        d.y += d.vy;
        if (d.y < -5) d.y = H + 5;

        const op = d.life < 0.2 ? d.life / 0.2 : d.life > 0.8 ? (1 - d.life) / 0.2 : 1;
        ctx.beginPath();
        ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
        ctx.fillStyle = d.color + (op * 0.6) + ')';
        ctx.fill();
      }

      // Étoiles filantes
      for (const s of shoots) {
        s.timer += 0.016;
        if (!s.active && s.timer > s.delay) {
          s.active = true;
          s.timer = 0;
          s.x = Math.random() * W * 0.7;
          s.y = Math.random() * H * 0.35;
          s.progress = 0;
        }
        if (!s.active) continue;

        s.progress += s.speed / 1000;
        if (s.progress >= 1) {
          s.active = false;
          s.timer = 0;
          s.delay = Math.random() * 10 + 4;
          continue;
        }

        const px = s.x + Math.cos(Math.PI / 4) * s.progress * s.len * 5;
        const py = s.y + Math.sin(Math.PI / 4) * s.progress * s.len * 5;
        const trail = ctx.createLinearGradient(px - s.len * 0.7, py - s.len * 0.7, px, py);
        trail.addColorStop(0, 'transparent');
        trail.addColorStop(0.6, s.color + '40');
        trail.addColorStop(1, s.color + 'DD');
        ctx.beginPath();
        ctx.moveTo(px - s.len * 0.7, py - s.len * 0.7);
        ctx.lineTo(px, py);
        ctx.strokeStyle = trail;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      raf = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={ref}
      aria-hidden="true"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
}
