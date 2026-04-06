/**
 * API client for Personal Finance Decision Engine backend.
 * Type-safe fetch wrapper with JWT auth management.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ---------- Types ----------

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  monthly_income: number;
  currency: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Transaction {
  id: number;
  user_id: number;
  date: string;
  amount: number;
  category: string;
  merchant: string | null;
  description: string | null;
  predicted_category: string | null;
  created_at: string;
}

export interface TransactionSummary {
  total_spending: number;
  transaction_count: number;
  category_breakdown: Record<string, number>;
  daily_average: number;
  top_merchants: { merchant: string; amount: number }[];
  month: string;
}

export interface RiskPrediction {
  overspend_probability: number;
  risk_level: string;
  days_remaining: number;
  current_spending: number;
  projected_spending: number;
  monthly_income: number;
}

export interface ForecastPoint {
  date: string;
  predicted_amount: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastResponse {
  forecast: ForecastPoint[];
  total_predicted: number;
  forecast_days: number;
  model_used: string;
  rmse: number | null;
  mape: number | null;
}

export interface PredictionResponse {
  category_predictions: {
    transaction_id: number;
    predicted_category: string;
    confidence: number;
  }[];
  risk: RiskPrediction;
  forecast: ForecastResponse;
}

export interface Recommendation {
  type: string;
  priority: string;
  message: string;
  confidence: number;
  category: string | null;
  amount: number | null;
}

export interface RecommendationResponse {
  recommendations: Recommendation[];
  generated_at: string;
  summary: string;
}

export interface FeatureImpact {
  feature: string;
  importance: number;
  direction: string;
  description: string;
}

export interface Explanation {
  recommendation_index: number;
  reasoning: string;
  feature_impacts: FeatureImpact[];
  contributing_factors: string[];
}

export interface ExplainResponse {
  explanations: Explanation[];
  model_metrics: Record<string, number>;
  feature_importance_global: Record<string, number>;
}

export interface ModelMetrics {
  classifier_accuracy: number;
  classifier_f1: number;
  risk_auc_roc: number;
  risk_f1: number;
  forecast_rmse: number | null;
  forecast_mape: number | null;
}

// ---------- Token Management ----------

let authToken: string | null = null;

export function setToken(token: string) {
  authToken = token;
  if (typeof window !== "undefined") {
    localStorage.setItem("finance_token", token);
  }
}

export function getToken(): string | null {
  if (authToken) return authToken;
  if (typeof window !== "undefined") {
    authToken = localStorage.getItem("finance_token");
  }
  return authToken;
}

export function clearToken() {
  authToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("finance_token");
    localStorage.removeItem("finance_user");
  }
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("finance_user");
  return raw ? JSON.parse(raw) : null;
}

export function setStoredUser(user: User) {
  if (typeof window !== "undefined") {
    localStorage.setItem("finance_user", JSON.stringify(user));
  }
}

// ---------- Fetch Wrapper ----------

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// ---------- Auth API ----------

export async function register(
  email: string,
  password: string,
  monthly_income: number,
  full_name?: string
): Promise<TokenResponse> {
  const data = await apiFetch<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, monthly_income, full_name }),
  });
  setToken(data.access_token);
  setStoredUser(data.user);
  return data;
}

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const data = await apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  setStoredUser(data.user);
  return data;
}

export async function getMe(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

// ---------- Transaction API ----------

export async function getTransactions(
  skip = 0,
  limit = 100
): Promise<Transaction[]> {
  return apiFetch<Transaction[]>(
    `/transactions?skip=${skip}&limit=${limit}`
  );
}

export async function getTransactionSummary(
  year?: number,
  month?: number
): Promise<TransactionSummary> {
  const params = new URLSearchParams();
  if (year) params.set("year", String(year));
  if (month) params.set("month", String(month));
  return apiFetch<TransactionSummary>(
    `/transactions/summary?${params.toString()}`
  );
}

export async function uploadTransactions(
  transactions: {
    date: string;
    amount: number;
    category: string;
    merchant?: string;
    description?: string;
  }[]
): Promise<Transaction[]> {
  return apiFetch<Transaction[]>("/transactions/bulk", {
    method: "POST",
    body: JSON.stringify({ transactions }),
  });
}

// ---------- Prediction API ----------

export async function getPredictions(
  forecastDays = 30
): Promise<PredictionResponse> {
  return apiFetch<PredictionResponse>(
    `/predict?forecast_days=${forecastDays}`
  );
}

// ---------- Recommendation API ----------

export async function getRecommendations(): Promise<RecommendationResponse> {
  return apiFetch<RecommendationResponse>("/recommend");
}

// ---------- Explain API ----------

export async function getExplanations(): Promise<ExplainResponse> {
  return apiFetch<ExplainResponse>("/explain");
}

export async function getModelMetrics(): Promise<ModelMetrics> {
  return apiFetch<ModelMetrics>("/explain/metrics");
}
