"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/ui/Sidebar";
import {
  getToken,
  getRecommendations,
  getExplanations,
  type RecommendationResponse,
  type ExplainResponse,
} from "@/lib/api";

export default function RecommendationsPage() {
  const router = useRouter();
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [explanations, setExplanations] = useState<ExplainResponse | null>(null);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.push("/");
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [recData, expData] = await Promise.allSettled([
        getRecommendations(),
        getExplanations(),
      ]);
      if (recData.status === "fulfilled") setRecommendations(recData.value);
      if (expData.status === "fulfilled") setExplanations(expData.value);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  const typeIcons: Record<string, string> = {
    alert: "🚨",
    warning: "⚠️",
    suggestion: "💡",
  };

  return (
    <div className="flex min-h-screen" style={{ background: "var(--color-background)" }}>
      <Sidebar activePage="recommendations" />

      <main className="flex-1 p-6 lg:p-8 ml-0 lg:ml-64 overflow-auto">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold" style={{ color: "var(--color-text-primary)" }}>
            Recommendations & Explanations
          </h1>
          <p style={{ color: "var(--color-text-secondary)" }}>
            AI-powered financial decisions with full transparency
          </p>
        </div>

        {/* Summary Banner */}
        {recommendations && (
          <div
            className="glass-card p-6 mb-6 animate-fade-in"
            style={{
              borderLeft: "4px solid var(--color-accent-emerald)",
            }}
          >
            <p className="font-medium" style={{ color: "var(--color-text-primary)" }}>
              {recommendations.summary}
            </p>
            <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
              Generated at {new Date(recommendations.generated_at).toLocaleString()}
            </p>
          </div>
        )}

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
          </div>
        )}

        {/* Recommendations List */}
        <div className="space-y-4 stagger-children">
          {recommendations?.recommendations.map((rec, idx) => {
            const explanation = explanations?.explanations[idx];
            const isExpanded = expandedIdx === idx;

            return (
              <div key={idx} className="glass-card overflow-hidden">
                <div
                  className="p-5 cursor-pointer transition-all hover:bg-opacity-50"
                  onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                  style={{ background: isExpanded ? "rgba(255,255,255,0.02)" : "transparent" }}
                >
                  <div className="flex items-start gap-4">
                    <span className="text-2xl">{typeIcons[rec.type] || "📌"}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold badge-${rec.priority}`}>
                          {rec.priority.toUpperCase()}
                        </span>
                        <span
                          className="px-2 py-0.5 rounded text-xs"
                          style={{
                            background: "rgba(59,130,246,0.15)",
                            color: "var(--color-accent-blue)",
                            border: "1px solid rgba(59,130,246,0.3)",
                          }}
                        >
                          {rec.type}
                        </span>
                        {rec.category && (
                          <span className="text-xs" style={{ color: "var(--color-text-muted)" }}>
                            {rec.category}
                          </span>
                        )}
                        <span className="ml-auto text-xs" style={{ color: "var(--color-text-muted)" }}>
                          Confidence: {(rec.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p style={{ color: "var(--color-text-primary)" }}>{rec.message}</p>
                    </div>
                    <span
                      className="transform transition-transform text-sm"
                      style={{
                        color: "var(--color-text-muted)",
                        transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
                      }}
                    >
                      ▼
                    </span>
                  </div>
                </div>

                {/* Expanded Explanation */}
                {isExpanded && explanation && (
                  <div
                    className="px-5 pb-5 border-t"
                    style={{
                      borderColor: "var(--color-border)",
                      background: "rgba(0,0,0,0.2)",
                    }}
                  >
                    <div className="pt-4 space-y-4">
                      {/* Reasoning */}
                      <div>
                        <h4 className="text-sm font-semibold mb-2 flex items-center gap-2" style={{ color: "var(--color-accent-emerald)" }}>
                          🧠 Why this recommendation?
                        </h4>
                        <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                          {explanation.reasoning}
                        </p>
                      </div>

                      {/* Feature Impacts */}
                      {explanation.feature_impacts.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold mb-2" style={{ color: "var(--color-accent-blue)" }}>
                            📊 Key Factors
                          </h4>
                          <div className="space-y-2">
                            {explanation.feature_impacts.map((fi, j) => (
                              <div
                                key={j}
                                className="flex items-center gap-3 p-2 rounded"
                                style={{ background: "var(--color-surface)" }}
                              >
                                <div className="flex-1">
                                  <p className="text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>
                                    {fi.feature}
                                  </p>
                                  <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
                                    {fi.description}
                                  </p>
                                </div>
                                <div className="flex items-center gap-2">
                                  <div
                                    className="h-2 rounded-full"
                                    style={{
                                      width: `${Math.max(20, fi.importance * 200)}px`,
                                      background:
                                        fi.direction === "positive"
                                          ? "var(--color-accent-rose)"
                                          : "var(--color-accent-emerald)",
                                    }}
                                  />
                                  <span className="text-xs font-mono" style={{ color: "var(--color-text-muted)" }}>
                                    {fi.importance.toFixed(3)}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Contributing Factors */}
                      {explanation.contributing_factors.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold mb-2" style={{ color: "var(--color-accent-amber)" }}>
                            📋 Contributing Factors
                          </h4>
                          <ul className="space-y-1">
                            {explanation.contributing_factors.map((factor, j) => (
                              <li
                                key={j}
                                className="flex items-center gap-2 text-sm"
                                style={{ color: "var(--color-text-secondary)" }}
                              >
                                <span style={{ color: "var(--color-accent-amber)" }}>•</span>
                                {factor}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Global Feature Importance */}
        {explanations && Object.keys(explanations.feature_importance_global).length > 0 && (
          <div className="glass-card p-6 mt-8 animate-fade-in">
            <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--color-text-primary)" }}>
              Global Feature Importance
            </h3>
            <div className="space-y-2">
              {Object.entries(explanations.feature_importance_global)
                .slice(0, 10)
                .map(([feature, importance]) => (
                  <div key={feature} className="flex items-center gap-3">
                    <span
                      className="text-sm w-48 truncate"
                      style={{ color: "var(--color-text-secondary)" }}
                    >
                      {feature.replace(/^(classifier_|risk_)/, "")}
                    </span>
                    <div className="flex-1 h-3 rounded-full overflow-hidden" style={{ background: "var(--color-surface)" }}>
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${Math.min(100, importance * 300)}%`,
                          background: "linear-gradient(90deg, var(--color-accent-blue), var(--color-accent-violet))",
                        }}
                      />
                    </div>
                    <span className="text-xs font-mono w-12 text-right" style={{ color: "var(--color-text-muted)" }}>
                      {importance.toFixed(3)}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Model Metrics */}
        {explanations && Object.keys(explanations.model_metrics).length > 0 && (
          <div className="glass-card p-6 mt-6 animate-fade-in">
            <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--color-text-primary)" }}>
              ML Model Evaluation Metrics
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {Object.entries(explanations.model_metrics).map(([key, val]) => (
                <div
                  key={key}
                  className="text-center p-4 rounded-lg"
                  style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}
                >
                  <p className="text-xs mb-1 capitalize" style={{ color: "var(--color-text-muted)" }}>
                    {key.replace(/_/g, " ")}
                  </p>
                  <p className="text-2xl font-bold" style={{ color: "var(--color-accent-emerald)" }}>
                    {typeof val === "number" ? (val < 1 && val > 0 ? (val * 100).toFixed(1) + "%" : val.toFixed(2)) : val}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div
                className="w-12 h-12 rounded-full border-4 border-t-transparent animate-spin mx-auto mb-4"
                style={{ borderColor: "var(--color-border)", borderTopColor: "transparent" }}
              />
              <p style={{ color: "var(--color-text-secondary)" }}>
                Generating insights...
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
