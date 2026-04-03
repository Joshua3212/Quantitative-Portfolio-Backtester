# Backend – Portfolio Backtester API

FastAPI backend that wraps the existing strategy implementations and exposes them over HTTP.

## Setup & run

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Interactive docs are available at <http://localhost:8000/docs>.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/strategies` | List all strategy configs with param metadata |
| `POST` | `/api/backtest` | Run a backtest and return chart-ready JSON |
| `GET`  | `/api/stock-info/{ticker}` | Company name, sector, summary |

### `POST /api/backtest` body

```json
{
  "ticker": "AAPL",
  "start_date": "2020-01-01",
  "end_date": "2024-01-01",
  "strategy": "moving_average",
  "params": { "short_window": 50, "long_window": 200 }
}
```
