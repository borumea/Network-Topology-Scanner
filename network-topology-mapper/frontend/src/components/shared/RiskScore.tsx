import { getRiskColor, getRiskLabel } from '../../lib/graph-utils';

interface Props {
  score: number;
  showBar?: boolean;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function RiskScore({ score, showBar = true, showLabel = true, size = 'md' }: Props) {
  const color = getRiskColor(score);
  const label = getRiskLabel(score);
  const pct = Math.round(score * 100);
  const segments = 10;
  const filled = Math.round((pct / 100) * segments);

  const textSize = size === 'sm' ? 'text-caption' : size === 'lg' ? 'text-subheading' : 'text-body-sm';
  const barHeight = size === 'sm' ? 'h-1' : size === 'lg' ? 'h-3' : 'h-2';

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className={`${textSize} font-mono font-bold`} style={{ color }}>
          {score.toFixed(2)}
        </span>
        {showLabel && (
          <span className="font-mono text-label uppercase tracking-[0.08em]" style={{ color }}>
            {label}
          </span>
        )}
      </div>
      {showBar && (
        <div className={`${barHeight} w-full flex gap-[2px]`}>
          {Array.from({ length: segments }).map((_, i) => (
            <div
              key={i}
              className={`${barHeight} flex-1`}
              style={{ backgroundColor: i < filled ? color : '#E8E8E8' }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
