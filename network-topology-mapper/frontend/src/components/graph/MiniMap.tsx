import { useEffect, useRef } from 'react';
import type { Core } from 'cytoscape';
import { DEVICE_TYPE_COLORS } from '../../lib/graph-utils';

interface Props {
  cy: Core | null;
}

export default function MiniMap({ cy }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!cy || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#1A1D28';
      ctx.fillRect(0, 0, width, height);

      const bb = cy.elements().boundingBox();
      if (bb.w === 0 || bb.h === 0) return;

      const padding = 10;
      const scaleX = (width - padding * 2) / bb.w;
      const scaleY = (height - padding * 2) / bb.h;
      const scale = Math.min(scaleX, scaleY);

      const offsetX = padding + (width - padding * 2 - bb.w * scale) / 2;
      const offsetY = padding + (height - padding * 2 - bb.h * scale) / 2;

      // Draw edges
      ctx.strokeStyle = 'rgba(71, 85, 105, 0.4)';
      ctx.lineWidth = 0.5;
      cy.edges().forEach((edge) => {
        const src = edge.source().position();
        const tgt = edge.target().position();
        ctx.beginPath();
        ctx.moveTo((src.x - bb.x1) * scale + offsetX, (src.y - bb.y1) * scale + offsetY);
        ctx.lineTo((tgt.x - bb.x1) * scale + offsetX, (tgt.y - bb.y1) * scale + offsetY);
        ctx.stroke();
      });

      // Draw nodes with device-type colors
      cy.nodes().forEach((node) => {
        const pos = node.position();
        const x = (pos.x - bb.x1) * scale + offsetX;
        const y = (pos.y - bb.y1) * scale + offsetY;
        const deviceType = node.data('device_type') as string;
        const color = DEVICE_TYPE_COLORS[deviceType as keyof typeof DEVICE_TYPE_COLORS] || '#6B7280';

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      });

      // Draw viewport rectangle
      const ext = cy.extent();
      const vx = (ext.x1 - bb.x1) * scale + offsetX;
      const vy = (ext.y1 - bb.y1) * scale + offsetY;
      const vw = ext.w * scale;
      const vh = ext.h * scale;

      ctx.strokeStyle = 'rgba(59, 130, 246, 0.6)';
      ctx.lineWidth = 1;
      ctx.strokeRect(vx, vy, vw, vh);
    };

    const interval = setInterval(draw, 500);
    draw();

    return () => clearInterval(interval);
  }, [cy]);

  return (
    <div className="absolute bottom-4 left-4 z-10">
      <canvas
        ref={canvasRef}
        width={150}
        height={100}
        className="rounded-lg border border-bg-tertiary bg-bg-secondary/80 backdrop-blur-sm cursor-pointer"
      />
    </div>
  );
}
