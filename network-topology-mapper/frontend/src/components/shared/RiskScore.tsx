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

  const textSize = size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-lg' : 'text-sm';
  const barHeight = size === 'sm' ? 'h-1' : size === 'lg' ? 'h-3' : 'h-2';

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className={`${textSize} font-mono font-semibold`} style={{ color }}>
          {score.toFixed(2)}
        </span>
        {showLabel && (
          <span className={`${textSize} font-medium uppercase`} style={{ color }}>
            {label}
          </span>
        )}
      </div>
      {showBar && (
        <div className={`${barHeight} w-full rounded-full bg-bg-tertiary overflow-hidden`}>
          <div
            className={`${barHeight} rounded-full transition-all duration-500`}
            style={{ width: `${pct}%`, backgroundColor: color }}
          />
        </div>
      )}
    </div>
  );
}
