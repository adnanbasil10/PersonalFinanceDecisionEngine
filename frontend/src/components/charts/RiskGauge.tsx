"use client";

interface Props {
  probability: number;
  level: string;
}

export default function RiskGauge({ probability, level }: Props) {
  const percentage = Math.round(probability * 100);
  const circumference = 2 * Math.PI * 80;
  const strokeDashoffset = circumference - (percentage / 100) * circumference * 0.75; // 270 degree arc

  const getColor = () => {
    if (probability > 0.7) return "#f43f5e";
    if (probability > 0.5) return "#f59e0b";
    if (probability > 0.3) return "#3b82f6";
    return "#10b981";
  };

  const getLevelText = () => {
    switch (level) {
      case "critical":
        return "Critical Risk";
      case "high":
        return "High Risk";
      case "medium":
        return "Moderate Risk";
      default:
        return "Low Risk";
    }
  };

  const color = getColor();

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-48">
        <svg viewBox="0 0 200 200" className="transform -rotate-135">
          {/* Background arc */}
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke="rgba(55,65,81,0.3)"
            strokeWidth="12"
            strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
            strokeLinecap="round"
          />
          {/* Value arc */}
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
            style={{
              filter: `drop-shadow(0 0 8px ${color}50)`,
            }}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="text-4xl font-bold"
            style={{ color }}
          >
            {percentage}%
          </span>
          <span className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>
            probability
          </span>
        </div>
      </div>

      <div className="text-center mt-2">
        <p className="font-semibold" style={{ color }}>
          {getLevelText()}
        </p>
        <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>
          of overspending this month
        </p>
      </div>
    </div>
  );
}
