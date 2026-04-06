"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { type ForecastPoint } from "@/lib/api";

interface Props {
  forecast: ForecastPoint[];
}

export default function ForecastChart({ forecast }: Props) {
  if (!forecast || forecast.length === 0) {
    return (
      <div className="flex items-center justify-center h-64" style={{ color: "var(--color-text-muted)" }}>
        No forecast data available
      </div>
    );
  }

  const data = forecast.map((p) => ({
    date: p.date,
    predicted: Math.round(p.predicted_amount),
    lower: Math.round(p.lower_bound),
    upper: Math.round(p.upper_bound),
  }));

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(55,65,81,0.5)" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#9ca3af", fontSize: 11 }}
            tickFormatter={(val) => {
              const d = new Date(val);
              return `${d.getDate()}/${d.getMonth() + 1}`;
            }}
          />
          <YAxis
            tick={{ fill: "#9ca3af", fontSize: 11 }}
            tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#f9fafb",
            }}
            formatter={(value: any, name: any) => {
              const labels: Record<string, string> = {
                predicted: "Predicted",
                upper: "Upper Bound",
                lower: "Lower Bound",
              };
              return [`₹${(value as number).toLocaleString()}`, labels[name as string] || name];
            }}
            labelFormatter={(label) => new Date(label).toLocaleDateString("en-IN")}
          />
          {/* Confidence band */}
          <Area
            type="monotone"
            dataKey="upper"
            stackId="band"
            stroke="none"
            fill="rgba(139,92,246,0.15)"
          />
          <Area
            type="monotone"
            dataKey="lower"
            stackId="band"
            stroke="none"
            fill="rgba(10,15,26,1)"
          />
          {/* Prediction line */}
          <Area
            type="monotone"
            dataKey="predicted"
            stroke="#8b5cf6"
            strokeWidth={2}
            fill="rgba(139,92,246,0.1)"
            dot={false}
            activeDot={{ r: 5, fill: "#8b5cf6" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
