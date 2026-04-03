"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  TrendingUp,
  AlertCircle,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  BarChart2,
  ExternalLink,
} from "lucide-react";
import {
  fetchStrategies,
  fetchStockInfo,
  runBacktest,
  type BacktestResponse,
  type ChartDataPoint,
  type IndicatorConfig,
  type StockInfo,
  type StrategyConfig,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ParamValues {
  [key: string]: number;
}

interface ProcessedDataPoint extends ChartDataPoint {
  buyPrice?: number | null;
  sellPrice?: number | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "2-digit" });
}

function formatPrice(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function processChartData(data: ChartDataPoint[]): ProcessedDataPoint[] {
  return data.map((d) => ({
    ...d,
    buyPrice: d.signal === 1 ? d.close : null,
    sellPrice: d.signal === -1 ? d.close : null,
  }));
}

// Thin the x-axis ticks so labels don't overlap
function tickFormatter(value: string, index: number, total: number): string {
  const step = Math.max(1, Math.floor(total / 8));
  if (index % step !== 0) return "";
  return formatDate(value);
}

// ---------------------------------------------------------------------------
// Custom dot renderers for buy / sell signals
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function BuyDot(props: any) {
  const { cx, cy } = props;
  if (cx == null || cy == null) return null;
  return (
    <polygon
      points={`${cx},${cy - 8} ${cx - 6},${cy + 4} ${cx + 6},${cy + 4}`}
      fill="#00dc82"
      stroke="#000"
      strokeWidth={1}
    />
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function SellDot(props: any) {
  const { cx, cy } = props;
  if (cx == null || cy == null) return null;
  return (
    <polygon
      points={`${cx},${cy + 8} ${cx - 6},${cy - 4} ${cx + 6},${cy - 4}`}
      fill="#ef4444"
      stroke="#000"
      strokeWidth={1}
    />
  );
}

// ---------------------------------------------------------------------------
// Custom tooltip
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || payload.length === 0) return null;

  const signal = payload[0]?.payload?.signal;
  const signalLabel =
    signal === 1 ? "🟢 Buy" : signal === -1 ? "🔴 Sell" : null;

  return (
    <div className="bg-surface-2 border border-border rounded-lg p-3 text-sm shadow-xl min-w-[160px]">
      <p className="text-secondary mb-2 font-medium">{formatDate(label)}</p>
      {payload.map(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (entry: any) =>
          entry.value != null &&
          entry.dataKey !== "buyPrice" &&
          entry.dataKey !== "sellPrice" ? (
            <div key={entry.dataKey} className="flex justify-between gap-4">
              <span style={{ color: entry.color }} className="truncate max-w-[100px]">
                {entry.name}
              </span>
              <span className="text-primary font-mono">
                {typeof entry.value === "number" ? entry.value.toFixed(2) : entry.value}
              </span>
            </div>
          ) : null
      )}
      {signalLabel && (
        <p className="mt-2 pt-2 border-t border-border font-semibold">{signalLabel}</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skeleton loaders
// ---------------------------------------------------------------------------

function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div className={`bg-surface-2 rounded-lg animate-pulse ${className ?? ""}`} />
  );
}

function ChartSkeleton() {
  return (
    <div className="space-y-3">
      <SkeletonBlock className="h-6 w-40" />
      <SkeletonBlock className="h-[380px]" />
      <div className="flex gap-3">
        <SkeletonBlock className="h-16 flex-1" />
        <SkeletonBlock className="h-16 flex-1" />
        <SkeletonBlock className="h-16 flex-1" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stats bar
// ---------------------------------------------------------------------------

function StatsBar({
  stats,
  currency,
}: {
  stats: BacktestResponse["stats"];
  currency: string;
}) {
  return (
    <div className="grid grid-cols-3 gap-3 mt-4">
      {[
        {
          label: "Total Signals",
          value: stats.total_signals,
          icon: <BarChart2 size={16} className="text-secondary" />,
          accent: "text-primary",
        },
        {
          label: "Buy Signals",
          value: stats.buy_signals,
          icon: <ArrowUpRight size={16} className="text-buy" />,
          accent: "text-buy",
        },
        {
          label: "Sell Signals",
          value: stats.sell_signals,
          icon: <ArrowDownRight size={16} className="text-sell" />,
          accent: "text-sell",
        },
      ].map((stat) => (
        <div key={stat.label} className="bg-surface-2 border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            {stat.icon}
            <span className="text-xs text-secondary uppercase tracking-wider">
              {stat.label}
            </span>
          </div>
          <p className={`text-2xl font-bold font-mono ${stat.accent}`}>
            {stat.value}
          </p>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stock info card
// ---------------------------------------------------------------------------

function StockInfoCard({
  info,
  ticker,
}: {
  info: StockInfo;
  ticker: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const summary = info.summary;
  const truncated = summary.length > 240 ? summary.slice(0, 240) + "…" : summary;

  return (
    <div className="bg-surface border border-border rounded-xl p-5 mb-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-lg font-semibold text-primary">{info.name}</h2>
            <span className="text-xs bg-surface-2 border border-border rounded px-2 py-0.5 text-secondary font-mono uppercase">
              {ticker}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs text-secondary">
            {info.sector && <span>{info.sector}</span>}
            {info.sector && info.industry && <span>·</span>}
            {info.industry && <span>{info.industry}</span>}
          </div>
        </div>
        {info.website && (
          <a
            href={info.website}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-secondary hover:text-primary transition-colors shrink-0"
          >
            <ExternalLink size={12} />
            Website
          </a>
        )}
      </div>
      {summary && (
        <p className="text-sm text-secondary mt-3 leading-relaxed">
          {expanded ? summary : truncated}
          {summary.length > 240 && (
            <button
              onClick={() => setExpanded((e) => !e)}
              className="ml-1 text-accent hover:text-accent-hover text-xs"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Backtest chart
// ---------------------------------------------------------------------------

function BacktestChart({
  data,
  indicators,
  currency,
}: {
  data: ProcessedDataPoint[];
  indicators: IndicatorConfig[];
  currency: string;
}) {
  const total = data.length;
  const primaryIndicators = indicators.filter((i) => !i.secondary);
  const secondaryIndicators = indicators.filter((i) => i.secondary);
  const hasSecondary = secondaryIndicators.length > 0;

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#1f1f1f" strokeDasharray="4 4" vertical={false} />

          <XAxis
            dataKey="date"
            tick={{ fill: "#888888", fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: "#333333" }}
            tickFormatter={(value, index) => tickFormatter(value, index, total)}
            interval="preserveStartEnd"
          />

          <YAxis
            yAxisId="primary"
            orientation="left"
            tick={{ fill: "#888888", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v.toFixed(0)}`}
            width={58}
          />

          {hasSecondary && (
            <YAxis
              yAxisId="secondary"
              orientation="right"
              tick={{ fill: "#888888", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => {
                if (Math.abs(v) < 1) return (v * 100).toFixed(1) + "%";
                return v >= 1e6
                  ? (v / 1e6).toFixed(1) + "M"
                  : v >= 1e3
                  ? (v / 1e3).toFixed(0) + "K"
                  : v.toFixed(0);
              }}
              width={60}
            />
          )}

          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: "16px", fontSize: "12px", color: "#888" }}
          />

          {/* Close price */}
          <Line
            yAxisId="primary"
            type="monotone"
            dataKey="close"
            name="Close"
            stroke="#ffffff"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4, fill: "#fff" }}
          />

          {/* Primary indicators (same scale as price) */}
          {primaryIndicators.map((ind) => (
            <Line
              key={ind.key}
              yAxisId="primary"
              type="monotone"
              dataKey={ind.key}
              name={ind.label}
              stroke={ind.color}
              strokeWidth={1.5}
              dot={false}
              strokeDasharray={ind.key.includes("high") || ind.key.includes("low") ? "4 4" : undefined}
              activeDot={{ r: 3 }}
            />
          ))}

          {/* Secondary indicators (different scale) */}
          {secondaryIndicators.map((ind) => (
            <Line
              key={ind.key}
              yAxisId="secondary"
              type="monotone"
              dataKey={ind.key}
              name={ind.label}
              stroke={ind.color}
              strokeWidth={1.5}
              dot={false}
              opacity={0.7}
              activeDot={{ r: 3 }}
            />
          ))}

          {/* Buy signal markers */}
          <Line
            yAxisId="primary"
            dataKey="buyPrice"
            name="Buy Signal"
            stroke="none"
            dot={<BuyDot />}
            activeDot={false}
            legendType="triangle"
            strokeWidth={0}
            connectNulls={false}
          />

          {/* Sell signal markers */}
          <Line
            yAxisId="primary"
            dataKey="sellPrice"
            name="Sell Signal"
            stroke="none"
            dot={<SellDot />}
            activeDot={false}
            legendType="triangle"
            strokeWidth={0}
            connectNulls={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Param input (slider + number display)
// ---------------------------------------------------------------------------

function ParamInput({
  label,
  name,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  name: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (name: string, value: number) => void;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center">
        <label className="text-xs text-secondary">{label}</label>
        <span className="text-xs font-mono text-primary bg-surface-2 border border-border rounded px-2 py-0.5">
          {step < 1 ? value.toFixed(1) : value}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) =>
          onChange(name, step < 1 ? parseFloat(e.target.value) : parseInt(e.target.value, 10))
        }
        className="w-full"
      />
      <div className="flex justify-between text-[10px] text-muted">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Dashboard
// ---------------------------------------------------------------------------

export default function Dashboard() {
  // ── Form state ───────────────────────────────────────────────────────────
  const [ticker, setTicker] = useState("AAPL");
  const [startDate, setStartDate] = useState("2020-01-01");
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [selectedStrategy, setSelectedStrategy] = useState("moving_average");
  const [paramValues, setParamValues] = useState<ParamValues>({});

  // ── Data state ───────────────────────────────────────────────────────────
  const [strategies, setStrategies] = useState<StrategyConfig[]>([]);
  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResponse | null>(null);
  const [processedData, setProcessedData] = useState<ProcessedDataPoint[]>([]);

  // ── UI state ─────────────────────────────────────────────────────────────
  const [loadingStrategies, setLoadingStrategies] = useState(true);
  const [loadingBacktest, setLoadingBacktest] = useState(false);
  const [loadingInfo, setLoadingInfo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [strategyError, setStrategyError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  // ── Load strategies on mount ─────────────────────────────────────────────
  useEffect(() => {
    fetchStrategies()
      .then((s) => {
        setStrategies(s);
        if (s.length > 0) {
          const first = s[0];
          setSelectedStrategy(first.id);
          const defaults: ParamValues = {};
          first.params.forEach((p) => (defaults[p.name] = p.default));
          setParamValues(defaults);
        }
      })
      .catch((e) => setStrategyError(e.message))
      .finally(() => setLoadingStrategies(false));
  }, []);

  // ── Update param defaults when strategy changes ──────────────────────────
  const handleStrategyChange = useCallback(
    (id: string) => {
      setSelectedStrategy(id);
      const config = strategies.find((s) => s.id === id);
      if (config) {
        const defaults: ParamValues = {};
        config.params.forEach((p) => (defaults[p.name] = p.default));
        setParamValues(defaults);
      }
    },
    [strategies]
  );

  const handleParamChange = useCallback((name: string, value: number) => {
    setParamValues((prev) => ({ ...prev, [name]: value }));
  }, []);

  // ── Run backtest ─────────────────────────────────────────────────────────
  const handleRunBacktest = useCallback(async () => {
    if (!ticker.trim()) return;

    // Cancel any in-flight request
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setLoadingBacktest(true);
    setLoadingInfo(true);
    setError(null);
    setBacktestResult(null);
    setStockInfo(null);

    // Fetch stock info and backtest in parallel
    const [infoResult, backtestPromise] = await Promise.allSettled([
      fetchStockInfo(ticker.trim().toUpperCase()),
      runBacktest({
        ticker: ticker.trim().toUpperCase(),
        start_date: startDate,
        end_date: endDate,
        strategy: selectedStrategy,
        params: paramValues,
      }),
    ]);

    if (infoResult.status === "fulfilled") {
      setStockInfo(infoResult.value);
    }
    setLoadingInfo(false);

    if (backtestPromise.status === "fulfilled") {
      const result = backtestPromise.value;
      setBacktestResult(result);
      setProcessedData(processChartData(result.chart_data));
    } else {
      setError((backtestPromise as PromiseRejectedResult).reason?.message ?? "Backtest failed.");
    }

    setLoadingBacktest(false);
  }, [ticker, startDate, endDate, selectedStrategy, paramValues]);

  // Submit on Enter in ticker field
  const handleTickerKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") handleRunBacktest();
    },
    [handleRunBacktest]
  );

  const currentStrategy = strategies.find((s) => s.id === selectedStrategy);
  const currency = stockInfo?.currency ?? "USD";

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* ── Header ── */}
      <header className="border-b border-border px-6 py-4 flex items-center gap-3 shrink-0">
        <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center">
          <TrendingUp size={16} className="text-black" />
        </div>
        <div>
          <h1 className="text-base font-semibold text-primary leading-none">
            Portfolio Backtester
          </h1>
          <p className="text-xs text-secondary mt-0.5">
            Quantitative strategy analysis
          </p>
        </div>
      </header>

      {/* ── Body ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ── Sidebar ── */}
        <aside className="w-72 shrink-0 border-r border-border overflow-y-auto p-5 space-y-6">
          {/* Ticker */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-secondary uppercase tracking-wider">
              Ticker Symbol
            </label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              onKeyDown={handleTickerKeyDown}
              placeholder="e.g. AAPL"
              className="w-full bg-surface border border-border rounded-lg px-3 py-2.5 text-sm text-primary placeholder-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition font-mono uppercase"
              maxLength={10}
            />
          </div>

          {/* Date range */}
          <div className="space-y-3">
            <label className="text-xs font-medium text-secondary uppercase tracking-wider">
              Date Range
            </label>
            <div className="space-y-2">
              <div>
                <label className="text-xs text-muted mb-1 block">Start</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-3 py-2.5 text-sm text-primary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition"
                />
              </div>
              <div>
                <label className="text-xs text-muted mb-1 block">End</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-3 py-2.5 text-sm text-primary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition"
                />
              </div>
            </div>
          </div>

          {/* Strategy selector */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-secondary uppercase tracking-wider">
              Strategy
            </label>
            {loadingStrategies ? (
              <SkeletonBlock className="h-10" />
            ) : strategyError ? (
              <p className="text-xs text-sell">{strategyError}</p>
            ) : (
              <select
                value={selectedStrategy}
                onChange={(e) => handleStrategyChange(e.target.value)}
                className="w-full bg-surface border border-border rounded-lg px-3 py-2.5 text-sm text-primary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition appearance-none cursor-pointer"
              >
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            )}
            {currentStrategy && (
              <p className="text-xs text-secondary leading-relaxed">
                {currentStrategy.description}
              </p>
            )}
          </div>

          {/* Strategy params */}
          {currentStrategy && currentStrategy.params.length > 0 && (
            <div className="space-y-4">
              <label className="text-xs font-medium text-secondary uppercase tracking-wider">
                Parameters
              </label>
              {currentStrategy.params.map((param) => (
                <ParamInput
                  key={param.name}
                  label={param.label}
                  name={param.name}
                  value={paramValues[param.name] ?? param.default}
                  min={param.min}
                  max={param.max}
                  step={param.step}
                  onChange={handleParamChange}
                />
              ))}
            </div>
          )}

          {/* Run button */}
          <button
            onClick={handleRunBacktest}
            disabled={loadingBacktest || !ticker.trim()}
            className="w-full bg-white text-black font-medium text-sm py-2.5 rounded-lg hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {loadingBacktest ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                Running…
              </>
            ) : (
              <>
                <TrendingUp size={14} />
                Run Backtest
              </>
            )}
          </button>
        </aside>

        {/* ── Main content ── */}
        <main className="flex-1 overflow-y-auto p-6">
          {/* Stock info */}
          {loadingInfo && (
            <div className="bg-surface border border-border rounded-xl p-5 mb-5">
              <div className="space-y-2">
                <SkeletonBlock className="h-5 w-48" />
                <SkeletonBlock className="h-3 w-32" />
                <SkeletonBlock className="h-3 w-full mt-3" />
                <SkeletonBlock className="h-3 w-5/6" />
              </div>
            </div>
          )}
          {!loadingInfo && stockInfo && (
            <StockInfoCard info={stockInfo} ticker={ticker.toUpperCase()} />
          )}

          {/* Error */}
          {error && (
            <div className="bg-surface border border-sell/30 rounded-xl p-5 mb-5 flex items-start gap-3">
              <AlertCircle size={16} className="text-sell shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-primary mb-0.5">Backtest failed</p>
                <p className="text-sm text-secondary">{error}</p>
              </div>
            </div>
          )}

          {/* Loading chart skeleton */}
          {loadingBacktest && <ChartSkeleton />}

          {/* Chart + stats */}
          {!loadingBacktest && backtestResult && processedData.length > 0 && (
            <div className="bg-surface border border-border rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-primary">
                    {currentStrategy?.name ?? "Strategy"} —{" "}
                    <span className="font-mono">{ticker.toUpperCase()}</span>
                  </h3>
                  <p className="text-xs text-secondary mt-0.5">
                    {startDate} → {endDate} · {processedData.length} trading days
                  </p>
                </div>
                <div className="flex items-center gap-3 text-xs text-secondary">
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-2 h-2 rounded-full bg-buy" />
                    Buy
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-2 h-2 rounded-full bg-sell" />
                    Sell
                  </span>
                </div>
              </div>

              <BacktestChart
                data={processedData}
                indicators={backtestResult.indicators}
                currency={currency}
              />

              <StatsBar stats={backtestResult.stats} currency={currency} />
            </div>
          )}

          {/* Empty state */}
          {!loadingBacktest && !backtestResult && !error && (
            <div className="flex flex-col items-center justify-center h-[60vh] text-center">
              <div className="w-14 h-14 rounded-2xl bg-surface border border-border flex items-center justify-center mb-4">
                <TrendingUp size={24} className="text-secondary" />
              </div>
              <h2 className="text-base font-medium text-primary mb-2">
                Ready to backtest
              </h2>
              <p className="text-sm text-secondary max-w-xs">
                Enter a ticker, choose a date range and strategy, then click{" "}
                <strong className="text-primary">Run Backtest</strong> to visualise
                signals on historical price data.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
