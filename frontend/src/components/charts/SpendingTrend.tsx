"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { type Transaction } from "@/lib/api";

interface Props {
  transactions: Transaction[];
}

export default function SpendingTrend({ transactions }: Props) {
  // Aggregate by date
  const dailyMap = new Map<string, number>();
  transactions.forEach((t) => {
    const key = t.date;
    dailyMap.set(key, (dailyMap.get(key) || 0) + t.amount);
  });

  const data = Array.from(dailyMap.entries())
    .map(([date, amount]) => ({
      date,
      amount: Math.round(amount),
    }))
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-30);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64" style={{ color: "var(--color-text-muted)" }}>
        No transaction data available
      </div>
    );
  }

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
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
            formatter={(value: any) => [`₹${(value as number).toLocaleString()}`, "Spending"]}
            labelFormatter={(label) => new Date(label).toLocaleDateString("en-IN")}
          />
          <Line
            type="monotone"
            dataKey="amount"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, fill: "#3b82f6" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
