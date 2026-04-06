"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/ui/Sidebar";
import MetricCard from "@/components/ui/MetricCard";
import SpendingTrend from "@/components/charts/SpendingTrend";
import CategoryBreakdown from "@/components/charts/CategoryBreakdown";
import ForecastChart from "@/components/charts/ForecastChart";
import RiskGauge from "@/components/charts/RiskGauge";
import {
  getToken,
  getStoredUser,
  getTransactionSummary,
  getPredictions,
  getRecommendations,
  getTransactions,
  type User,
  type TransactionSummary,
  type PredictionResponse,
  type RecommendationResponse,
  type Transaction,
} from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [summary, setSummary] = useState<TransactionSummary | null>(null);
  const [predictions, setPredictions] = useState<PredictionResponse | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/");
      return;
    }

    const stored = getStoredUser();
    if (stored) setUser(stored);

    loadData();
  }, [router]);

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [summaryData, predData, recData, txnData] = await Promise.allSettled([
        getTransactionSummary(),
        getPredictions(30),
        getRecommendations(),
        getTransactions(0, 50),
      ]);

      if (summaryData.status === "fulfilled") setSummary(summaryData.value);
      if (predData.status === "fulfilled") setPredictions(predData.value);
      if (recData.status === "fulfilled") setRecommendations(recData.value);
      if (txnData.status === "fulfilled") setTransactions(txnData.value);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const riskProb = predictions?.risk?.overspend_probability ?? 0;
  const riskLevel = predictions?.risk?.risk_level ?? "low";

  return (
    <div className="flex min-h-screen" style={{ background: "var(--color-background)" }}>
      <Sidebar activePage="dashboard" />

      <main className="flex-1 p-6 lg:p-8 ml-0 lg:ml-64 overflow-auto">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold" style={{ color: "var(--color-text-primary)" }}>
            Financial Dashboard
          </h1>
          <p style={{ color: "var(--color-text-secondary)" }}>
            {user ? `Welcome back, ${user.full_name || user.email}` : "Loading..."}
          </p>
        </div>

        {error && (
          <div
            className="mb-6 p-4 rounded-lg"
            style={{
              background: "rgba(244,63,94,0.1)",
              color: "var(--color-accent-rose)",
              border: "1px solid rgba(244,63,94,0.2)",
            }}
          >
            {error}
            <p className="text-sm mt-1 opacity-70">
              Make sure the backend is running and models are trained.
            </p>
          </div>
        )}

        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-8 stagger-children">
          <MetricCard
            title="Total Spending"
            value={summary ? `₹${summary.total_spending.toLocaleString()}` : "—"}
            subtitle={summary ? `${summary.transaction_count} transactions` : ""}
            gradient="gradient-blue"
            icon="💰"
          />
          <MetricCard
            title="Daily Average"
            value={summary ? `₹${summary.daily_average.toLocaleString()}` : "—"}
            subtitle={summary?.month || ""}
            gradient="gradient-violet"
            icon="📅"
          />
          <MetricCard
            title="Risk Level"
            value={riskLevel.toUpperCase()}
            subtitle={`${(riskProb * 100).toFixed(0)}% overspend probability`}
            gradient={riskProb > 0.7 ? "gradient-rose" : riskProb > 0.4 ? "gradient-amber" : "gradient-emerald"}
            icon="⚡"
          />
          <MetricCard
            title="Monthly Income"
            value={user ? `₹${user.monthly_income.toLocaleString()}` : "—"}
            subtitle={summary ? `${((1 - summary.total_spending / (user?.monthly_income || 1)) * 100).toFixed(0)}% remaining` : ""}
            gradient="gradient-emerald"
            icon="🏦"
          />
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2 glass-card p-6 animate-fade-in">
            <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--color-text-primary)" }}>
              Spending Trend
            </h3>
            <SpendingTrend transactions={transactions} />
          </div>
          <div className="glass-card p-6 animate-fade-in">
            <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--color-text-primary)" }}>
              Category Breakdown
            </h3>
            <CategoryBreakdown data={summary?.category_breakdown || {}} />
          </div>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2 glass-card p-6 animate-fade-in">
            <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--color-text-primary)" }}>
              Spending Forecast ({predictions?.forecast?.model_used || "Loading..."})
            </h3>
            <ForecastChart forecast={predictions?.forecast?.forecast || []} />
          </div>
          <div className="glass-card p-6 flex flex-col items-center justify-center animate-fade-in">
            <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--color-text-primary)" }}>
              Overspend Risk
            </h3>
            <RiskGauge probability={riskProb} level={riskLevel} />
          </div>
        </div>

        {/* Recommendations Preview */}
        {recommendations && recommendations.recommendations.length > 0 && (
          <div className="glass-card p-6 mb-6 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{ color: "var(--color-text-primary)" }}>
                Top Recommendations
              </h3>
              <button
                onClick={() => router.push("/dashboard/recommendations")}
                className="text-sm px-4 py-2 rounded-lg transition-all hover:opacity-80"
                style={{
                  background: "rgba(16,185,129,0.15)",
                  color: "var(--color-accent-emerald)",
                  border: "1px solid rgba(16,185,129,0.3)",
                }}
              >
                View All →
              </button>
            </div>
            <div className="space-y-3">
              {recommendations.recommendations.slice(0, 3).map((rec, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-4 rounded-lg"
                  style={{
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                  }}
                >
                  <span
                    className={`px-2 py-1 rounded text-xs font-semibold badge-${rec.priority}`}
                  >
                    {rec.priority.toUpperCase()}
                  </span>
                  <p className="text-sm flex-1" style={{ color: "var(--color-text-secondary)" }}>
                    {rec.message}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Model Metrics */}
        {predictions && (
          <div className="glass-card p-6 animate-fade-in">
            <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--color-text-primary)" }}>
              Model Performance
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {predictions.forecast?.rmse != null && (
                <div className="text-center p-3 rounded-lg" style={{ background: "var(--color-surface)" }}>
                  <p className="text-xs mb-1" style={{ color: "var(--color-text-muted)" }}>Forecast RMSE</p>
                  <p className="text-xl font-bold" style={{ color: "var(--color-accent-blue)" }}>
                    {predictions.forecast.rmse.toFixed(1)}
                  </p>
                </div>
              )}
              {predictions.forecast?.mape != null && (
                <div className="text-center p-3 rounded-lg" style={{ background: "var(--color-surface)" }}>
                  <p className="text-xs mb-1" style={{ color: "var(--color-text-muted)" }}>Forecast MAPE</p>
                  <p className="text-xl font-bold" style={{ color: "var(--color-accent-violet)" }}>
                    {predictions.forecast.mape.toFixed(1)}%
                  </p>
                </div>
              )}
              <div className="text-center p-3 rounded-lg" style={{ background: "var(--color-surface)" }}>
                <p className="text-xs mb-1" style={{ color: "var(--color-text-muted)" }}>Risk Score</p>
                <p className="text-xl font-bold" style={{ color: riskProb > 0.7 ? "var(--color-accent-rose)" : "var(--color-accent-emerald)" }}>
                  {(riskProb * 100).toFixed(0)}%
                </p>
              </div>
              <div className="text-center p-3 rounded-lg" style={{ background: "var(--color-surface)" }}>
                <p className="text-xs mb-1" style={{ color: "var(--color-text-muted)" }}>Forecast Model</p>
                <p className="text-xl font-bold" style={{ color: "var(--color-accent-amber)" }}>
                  {predictions.forecast?.model_used === "prophet" ? "Prophet" : "Ridge"}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div
                className="w-12 h-12 rounded-full border-4 border-t-transparent animate-spin mx-auto mb-4"
                style={{ borderColor: "var(--color-border)", borderTopColor: "transparent" }}
              />
              <p style={{ color: "var(--color-text-secondary)" }}>Loading your financial data...</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
