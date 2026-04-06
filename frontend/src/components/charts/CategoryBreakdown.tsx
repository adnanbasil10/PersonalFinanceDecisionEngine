"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface Props {
  data: Record<string, number>;
}

const COLORS = [
  "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#f43f5e",
  "#06b6d4", "#ec4899", "#84cc16", "#6366f1", "#14b8a6",
  "#f97316", "#a855f7", "#ef4444", "#22c55e", "#eab308",
  "#64748b",
];

export default function CategoryBreakdown({ data }: Props) {
  const chartData = Object.entries(data)
    .map(([name, value]) => ({ name, value: Math.round(value) }))
    .sort((a, b) => b.value - a.value);

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64" style={{ color: "var(--color-text-muted)" }}>
        No category data available
      </div>
    );
  }

  const total = chartData.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={85}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((_, idx) => (
              <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#f9fafb",
            }}
            formatter={(value: any, name: any) => [
              `₹${(value as number).toLocaleString()} (${(((value as number) / total) * 100).toFixed(1)}%)`,
              name,
            ]}
          />
          <Legend
            formatter={(value) => (
              <span style={{ color: "#9ca3af", fontSize: "11px" }}>{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
