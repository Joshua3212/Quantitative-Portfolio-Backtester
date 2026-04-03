const API_BASE = "http://localhost:8000";

export interface StrategyParam {
  name: string;
  label: string;
  default: number;
  min: number;
  max: number;
  step: number;
  type: "number";
}

export interface StrategyConfig {
  id: string;
  name: string;
  description: string;
  params: StrategyParam[];
}

export interface IndicatorConfig {
  key: string;
  label: string;
  secondary: boolean;
  color: string;
}

export interface ChartDataPoint {
  date: string;
  close: number | null;
  signal: number;
  [key: string]: number | null | string | undefined;
}

export interface BacktestStats {
  total_signals: number;
  buy_signals: number;
  sell_signals: number;
}

export interface BacktestResponse {
  chart_data: ChartDataPoint[];
  indicators: IndicatorConfig[];
  stats: BacktestStats;
}

export interface StockInfo {
  name: string;
  website: string;
  summary: string;
  sector: string;
  industry: string;
  currency: string;
}

export interface BacktestRequest {
  ticker: string;
  start_date: string;
  end_date: string;
  strategy: string;
  params: Record<string, number>;
}

export async function fetchStrategies(): Promise<StrategyConfig[]> {
  const res = await fetch(`${API_BASE}/api/strategies`);
  if (!res.ok) throw new Error(`Failed to fetch strategies: ${res.statusText}`);
  return res.json();
}

export async function fetchStockInfo(ticker: string): Promise<StockInfo> {
  const res = await fetch(`${API_BASE}/api/stock-info/${encodeURIComponent(ticker)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? res.statusText);
  }
  return res.json();
}

export async function runBacktest(req: BacktestRequest): Promise<BacktestResponse> {
  const res = await fetch(`${API_BASE}/api/backtest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? res.statusText);
  }
  return res.json();
}
