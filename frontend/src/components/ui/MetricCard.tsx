interface Props {
  title: string;
  value: string;
  subtitle: string;
  gradient: string;
  icon: string;
}

export default function MetricCard({ title, value, subtitle, gradient, icon }: Props) {
  return (
    <div
      className="glass-card p-5 relative overflow-hidden group cursor-default"
    >
      {/* Gradient accent */}
      <div
        className={`absolute top-0 right-0 w-24 h-24 ${gradient} opacity-20 rounded-bl-full transition-all group-hover:opacity-30 group-hover:w-28 group-hover:h-28`}
      />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium uppercase tracking-wider" style={{ color: "var(--color-text-muted)" }}>
            {title}
          </span>
          <span className="text-xl">{icon}</span>
        </div>
        <p className="text-2xl font-bold mb-1" style={{ color: "var(--color-text-primary)" }}>
          {value}
        </p>
        <p className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
          {subtitle}
        </p>
      </div>
    </div>
  );
}
