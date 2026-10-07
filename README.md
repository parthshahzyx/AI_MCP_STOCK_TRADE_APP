# AI MCP Stock Trade App

An end-to-end AI-powered stock trading platform built on Databricks Lakebase Postgres, combining an MCP trading server, a Flask dashboard, and a news ingestion + vector embeddings pipeline for RAG-based context engineering.

## Architecture

```
ai-mcp-stock-trade-app/
├── mcp_server/              # MCP trading server (FastMCP + Alpaca API)
│   ├── alpaca_mcp_server.py  # 8+ trading tools exposed via MCP
│   ├── alpaca_broker.py      # Alpaca API wrapper (live trading)
│   ├── paper_broker.py       # Paper trading simulation
│   ├── massive_broker.py     # Massive news API integration
│   ├── lakebase.py           # Lakebase Postgres helper + tracing
│   ├── schema_tracing.sql    # agent_sessions + mcp_traces tables
│   ├── schema_watchlist.sql  # Watchlist table schema
│   ├── test_watchlist.py     # Watchlist tool tests
│   └── app.yaml              # Databricks App deployment config
├── dashboard/               # Flask web dashboard (paper trading)
│   ├── app.py                # Trading dashboard + portfolio UI
│   ├── alpaca_broker.py      # Alpaca API wrapper
│   ├── paper_broker.py       # Paper trading logic
│   ├── lakebase.py           # Lakebase Postgres helper
│   ├── templates/            # HTML templates (index)
│   └── app.yaml              # Databricks App deployment config
├── news_app/                # Flask news watchlist + semantic search
│   ├── app.py                # Watchlist UI + news sync + semantic search
│   ├── massive_client.py     # Massive.com API client (news fetching)
│   ├── lakebase.py           # Lakebase Postgres helper
│   ├── templates/            # HTML templates (index, search)
│   ├── app.yaml              # Databricks App deployment config
│   └── requirements.txt     # Python deps (sentence-transformers, etc.)
├── notebooks/              # News ingestion + embeddings pipeline
│   └── ingest_ticker_news_embeddings  # Fetches news, computes vector embeddings
├── sql/                    # Lakebase table setup scripts
│   ├── 01_setup_news_table.sql           # ticker_news_documents
│   ├── 02_setup_embeddings_table.sql     # ticker_news_embeddings (pgvector)
│   ├── 03_setup_chunk_embeddings_table.sql # ticker_news_chunk_embeddings
│   └── README.md                         # Setup instructions
├── resources/              # Databricks Asset Bundle (scheduled job)
│   └── ingest_ticker_news_embeddings_job.yml
├── databricks.yml          # DABs bundle config
├── setup_secrets.py        # One-time Databricks secret setup
├── requirements.txt
├── LICENSE
└── .env.example
```

## What This Project Does

### 1. MCP Trading Server (`mcp_server/`)
A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes trading tools to AI agents via the Model Context Protocol:

- **get_quote** — Get real-time stock quotes
- **place_trade** — Place buy/sell orders (paper or live)
- **get_positions** — View current portfolio positions
- **get_account_summary** — Account balance and buying power
- **get_order_history** — Recent order history
- **get_balance** — Cash balance check
- **get_current_user** — Authenticated user info
- **add_to_watchlist / get_watchlist / remove_from_watchlist** — Manage tracked tickers

Every tool call is traced to the `mcp_traces` table in Lakebase with session tracking via `agent_sessions`, providing full observability of AI agent interactions.

### 2. Paper Trading Dashboard (`dashboard/`)
A web UI for monitoring a paper-trading portfolio, viewing positions and orders, and tracking what the MCP agent is doing to the Alpaca paper-trading account. Deployed as a Databricks App with OAuth2 authentication.

### 3. News Watchlist + Semantic Search (`news_app/`)
A Flask web app that lets you manage a stock watchlist, sync news from the Massive API into Lakebase, and perform semantic similarity search over news articles using pgvector embeddings. This is the human-facing frontend for the news/embeddings pipeline.

- **Watchlist management** — Add/remove tracked tickers, stored in the `watchlist` table
- **News sync** — Fetch recent news from Massive API and upsert into `ticker_news_documents`
- **Semantic search** — Search news articles by meaning (not keywords) using vector similarity over the `ticker_news_embeddings` table

### 4. News Ingestion + Embeddings Pipeline (`notebooks/` + `sql/`)
A scheduled Databricks notebook that:

1. Reads tracked tickers from the `watchlist` table in Lakebase
2. Fetches recent news from the Massive API (rate-limited for free tier)
3. Upserts articles into `ticker_news_documents`
4. Computes 384-dim sentence embeddings (`all-MiniLM-L6-v2`) and stores them in `ticker_news_embeddings` via pgvector
5. Fetches full article bodies, splits into overlapping chunks, and writes chunk-level embeddings to `ticker_news_chunk_embeddings` for fine-grained RAG retrieval

The job is deployable via Databricks Asset Bundles: `databricks bundle deploy -t dev`

## Project Evolution

This project was built across three iterative phases:

| Phase | Focus | Key additions |
| --- | --- | --- |
| **Day 1** | Lakebase + Massive API basics | Flask watchlist app, `massive_client.py`, `lakebase.py` connection helper |
| **Day 2** | Context engineering / RAG | News ingestion notebook, pgvector embeddings, semantic search UI, DABs scheduling |
| **Day 3** | MCP trading + observability | FastMCP trading server, Alpaca integration, tool-call tracing, paper-trading dashboard |

Each phase's code is preserved in its respective component directory (`news_app/` for Days 1-2, `mcp_server/` + `dashboard/` for Day 3).

## Tech Stack

| Component | Technology |
| --- | --- |
| Database | Databricks Lakebase Postgres (with pgvector) |
| Trading API | Alpaca Markets API |
| News API | Massive.com API |
| MCP Server | FastMCP (Python) |
| Web Dashboard | Flask + Starlette |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Article Extraction | trafilatura |
| Deployment | Databricks Apps + Databricks Asset Bundles |
| Secrets | Databricks Secret Scopes |

## Setup

### Prerequisites
- Databricks workspace with Lakebase Postgres enabled
- Alpaca API key (paper or live trading)
- Massive API key (for news ingestion)
- Databricks CLI configured

### 1. Configure Secrets
```bash
python setup_secrets.py
```
This creates Databricks secret scopes for `database` (Lakebase URL, Alpaca keys) and `massive` (API key).

### 2. Set Up Lakebase Tables
Run the SQL scripts in `sql/` against your Lakebase Postgres database in order:
1. `01_setup_news_table.sql` — Creates `ticker_news_documents`
2. `02_setup_embeddings_table.sql` — Creates `ticker_news_embeddings` (replace `{{EMBEDDING_DIM}}` with 384)
3. `03_setup_chunk_embeddings_table.sql` — Creates `ticker_news_chunk_embeddings` (same dimension)

Also run `mcp_server/schema_tracing.sql` and `mcp_server/schema_watchlist.sql` for the tracing and watchlist tables.

### 3. Deploy the MCP Trading Server
```bash
cd mcp_server
databricks apps deploy mcp-trading-server
```

### 4. Deploy the Paper Trading Dashboard
```bash
cd dashboard
databricks apps deploy trading-dashboard
```

### 5. Deploy the News Watchlist App
```bash
cd news_app
databricks apps deploy news-watchlist
```

### 6. Deploy the News Ingestion Job (optional)
```bash
databricks bundle deploy -t dev
databricks bundle run ingest_ticker_news_embeddings_job -t dev
```

## License

See [LICENSE](LICENSE).