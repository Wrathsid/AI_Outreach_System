'use client';

import { useEffect, useRef } from 'react';

export default function NeuralBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let w = canvas.width = window.innerWidth;
    let h = canvas.height = window.innerHeight;
    
    // Neural Nodes
    const nodes: { x: number, y: number, vx: number, vy: number, radius: number }[] = [];
    const nodeCount = 50; 
    
    for (let i = 0; i < nodeCount; i++) {
        nodes.push({
            x: Math.random() * w,
            y: Math.random() * h,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            radius: Math.random() * 1.5 + 0.5
        });
    }

    const draw = () => {
        ctx.clearRect(0, 0, w, h);
        
        // Update and Draw Nodes
        ctx.fillStyle = 'rgba(100, 200, 255, 0.4)';
        ctx.strokeStyle = 'rgba(100, 200, 255, 0.15)'; // Faint connection lines

        nodes.forEach((node, i) => {
            node.x += node.vx;
            node.y += node.vy;

            // Bounce off edges
            if (node.x < 0 || node.x > w) node.vx *= -1;
            if (node.y < 0 || node.y > h) node.vy *= -1;

            ctx.beginPath();
            ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
            ctx.fill();

            // Connect nearby nodes
            for (let j = i + 1; j < nodes.length; j++) {
                const other = nodes[j];
                const dx = node.x - other.x;
                const dy = node.y - other.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 150) {
                    ctx.beginPath();
                    ctx.moveTo(node.x, node.y);
                    ctx.lineTo(other.x, other.y);
                    ctx.lineWidth = 1 - (dist / 150);
                    ctx.stroke();
                }
            }
        });

        requestAnimationFrame(draw);
    };

    const handleResize = () => {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);
    const animId = requestAnimationFrame(draw);

    return () => {
        window.removeEventListener('resize', handleResize);
        cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-0">
        {/* Deep Space Background */}
        <div className="absolute inset-0 bg-[#050508]"></div>
        
        {/* Radial Pulse */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80vw] h-[80vh] bg-blue-900/10 blur-[120px] rounded-full animate-pulse-glow"></div>
        
        {/* Canvas Mesh */}
        <canvas ref={canvasRef} className="absolute inset-0 opacity-40" />
    </div>
  );
}
