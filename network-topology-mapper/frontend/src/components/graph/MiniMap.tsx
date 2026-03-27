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
      ctx.fillStyle = '#19191B';
      ctx.fillRect(0, 0, width, height);

      const bb = cy.elements().boundingBox();
      if (bb.w === 0 || bb.h === 0) return;

      const padding = 8;
      const scaleX = (width - padding * 2) / bb.w;
      const scaleY = (height - padding * 2) / bb.h;
      const scale = Math.min(scaleX, scaleY);
      const offsetX = padding + (width - padding * 2 - bb.w * scale) / 2;
      const offsetY = padding + (height - padding * 2 - bb.h * scale) / 2;

      ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
      ctx.lineWidth = 0.5;
      cy.edges().forEach((edge) => {
        const src = edge.source().position();
        const tgt = edge.target().position();
        ctx.beginPath();
        ctx.moveTo((src.x - bb.x1) * scale + offsetX, (src.y - bb.y1) * scale + offsetY);
        ctx.lineTo((tgt.x - bb.x1) * scale + offsetX, (tgt.y - bb.y1) * scale + offsetY);
        ctx.stroke();
      });

      cy.nodes().forEach((node) => {
        const pos = node.position();
        const x = (pos.x - bb.x1) * scale + offsetX;
        const y = (pos.y - bb.y1) * scale + offsetY;
        const deviceType = node.data('device_type') as string;
        ctx.fillStyle = DEVICE_TYPE_COLORS[deviceType as keyof typeof DEVICE_TYPE_COLORS] || '#5C5C5F';
        ctx.beginPath();
        ctx.arc(x, y, 2.5, 0, Math.PI * 2);
        ctx.fill();
      });

      const ext = cy.extent();
      ctx.strokeStyle = 'rgba(99, 102, 241, 0.4)';
      ctx.lineWidth = 1;
      ctx.strokeRect(
        (ext.x1 - bb.x1) * scale + offsetX,
        (ext.y1 - bb.y1) * scale + offsetY,
        ext.w * scale,
        ext.h * scale
      );
    };

    const interval = setInterval(draw, 500);
    draw();
    return () => clearInterval(interval);
  }, [cy]);

  return (
    <div className="absolute bottom-4 left-4 z-10">
      <canvas
        ref={canvasRef}
        width={140}
        height={90}
        className="rounded-lg border border-border bg-bg-secondary"
      />
    </div>
  );
}
