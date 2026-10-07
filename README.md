# AI MCP Stock Trade App

Welcome to the **AI Trading Agent App** — an end-to-end AI-powered trading platform built on Databricks. The AI agent reaches MCP tools through a custom MCP server to assist users with trading stock assets. Using RAG context engineering to research, learn, and stay up to speed on the markets.

## Why I Built It

I wanted hands-on experience with the different elements behind production AI agents — understanding how the brain (LLM) decides which tools to call (MCP), how agents interact with external APIs (Alpaca, Massive), and how to build a full-stack system with a database (Lakebase Postgres), backend (MCP server), and frontend (Flask dashboard) that all talk to each other. This project covers the full lifecycle- from ingesting market news and computing vector embeddings, to deploying an AI agent that can place real paper trades, to building a live dashboard that monitors everything.

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
├── combined_app/            # Unified Flask app (watchlist + dashboard + search)
│   ├── app.py                # All routes: watchlist, trading, search
│   ├── alpaca_broker.py      # Alpaca API wrapper
│   ├── lakebase.py           # Lakebase Postgres helper
│   ├── massive_client.py     # Massive.com API client
│   ├── templates/            # HTML templates (index, search)
│   ├── app.yaml              # Databricks App config
│   └── requirements.txt
├── news_app/                # Standalone news watchlist + semantic search
│   ├── app.py                # Watchlist UI + news sync + semantic search
│   ├── massive_client.py     # Massive.com API client (news fetching)
│   ├── lakebase.py           # Lakebase Postgres helper
│   ├── templates/            # HTML templates (index, search)
│   ├── app.yaml              # Databricks App deployment config
│   └── requirements.txt     # Python deps (sentence-transformers, etc.)
├── dashboard/               # Standalone paper trading dashboard
│   ├── app.py                # Trading dashboard + portfolio UI
│   ├── alpaca_broker.py      # Alpaca API wrapper
│   ├── paper_broker.py       # Paper trading logic
│   ├── lakebase.py           # Lakebase Postgres helper
│   ├── templates/            # HTML templates (index)
│   └── app.yaml              # Databricks App deployment config
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
├── LICENSE
└── .env.example
```

## Deployed Apps

This project runs as **3 Databricks Apps**:

| App | Purpose |

| `mcp-trading-server` | MCP trading server — AI agent calls its tools to trade | 

| `databricks-day-1` | Combined Flask app — watchlist, trading dashboard, semantic search |

| `agent-stock-trader` | Agent Bricks AI agent — prompts the MCP server in natural language |

## What This Project Does

### 1. MCP Trading Server (`mcp_server/`)
A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes trading tools to AI agents via the Model Context Protocol:

* **get_quote** — Get real-time stock quotes from Massive API
* **place_trade** — Place buy/sell orders on Alpaca paper account
* **get_positions** — View current portfolio positions
* **get_account_summary** — Account balance and buying power
* **get_order_history** — Recent order history
* **get_balance** — Cash balance check
* **get_current_user** — Authenticated user info
* **add_to_watchlist / get_watchlist / remove_from_watchlist** — Manage tracked tickers

Every tool call is traced to the `mcp_traces` table in Lakebase with session tracking via `agent_sessions`, providing full observability of AI agent interactions.

### 2. Combined App (`combined_app/`)
A unified Flask web app deployed as a Databricks App with OAuth2 authentication. It combines three features in one UI:

* **Watchlist management** — Add/remove tracked tickers, fetch live prices from Massive API, stored in the `watchlist` table
* **Paper trading dashboard** — Live view of Alpaca paper account: cash balance, market value, open positions, recent orders. Auto-refreshes every 10 seconds so trades placed by the AI agent appear in real time
* **Semantic search** — Search news articles by meaning (not keywords) using pgvector cosine similarity over 384-dim embeddings. Search across 1,664 chunk embeddings from 426 news articles

### 3. News Ingestion + Embeddings Pipeline (`notebooks/` + `sql/`)
A scheduled Databricks notebook that:

1. Reads tracked tickers from the `watchlist` table in Lakebase
2. Fetches recent news from the Massive API (rate-limited for free tier)
3. Upserts articles into `ticker_news_documents`
4. Computes 384-dim sentence embeddings (`all-MiniLM-L6-v2`) and stores them in `ticker_news_embeddings` via pgvector
5. Fetches full article bodies, splits into overlapping chunks, and writes chunk-level embeddings to `ticker_news_chunk_embeddings` for fine-grained RAG retrieval

The job runs daily at 6 AM UTC and is deployable via Databricks Asset Bundles: `databricks bundle deploy -t dev`

## Tech Stack

| Component | Technology |
| --- | --- |
| Database | Databricks Lakebase Postgres (with pgvector) |
| Trading API | Alpaca Markets API (paper trading) |
| News API | Massive.com API |
| MCP Server | FastMCP (Python) |
| AI Agent | Databricks Agent Bricks |
| Web App | Flask + Starlette (Databricks Apps) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Article Extraction | trafilatura |
| Deployment | Databricks Apps + Databricks Asset Bundles |
| Secrets | Databricks Secret Scopes |
| Version Control | Git (GitHub) |

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
Deploy from the `mcp_server/` directory as a Databricks App.

### 4. Deploy the Combined App
Deploy from the `combined_app/` directory as a Databricks App (from Git, branch `main`, source path `combined_app`).

### 5. Deploy the News Ingestion Job (optional)
```bash
databricks bundle deploy -t dev
databricks bundle run ingest_ticker_news_embeddings_job -t dev
```

## What I Learned

* **MCP Protocol** — How to build a custom MCP server with FastMCP that exposes tools an AI agent can discover and call autonomously
* **RAG / Context Engineering** — Building a full news ingestion pipeline with sentence embeddings and pgvector for semantic search over financial news
* **Lakebase Postgres** — Using Databricks' managed Postgres with pgvector for vector similarity search, working with psycopg2, and managing schemas across multiple tables
* **Agent Observability** — Designing tracing tables (`mcp_traces`, `agent_sessions`) to log every tool call an AI agent makes, for debugging and audit
* **Databricks Apps** — Deploying Flask web apps on Databricks with OAuth2 authentication, secret scopes, and environment variable management
* **DABs** — Using Databricks Asset Bundles to define and schedule the news ingestion job as infrastructure-as-code
* **Integration Architecture** — Connecting 4 external systems (Alpaca, Massive, Lakebase, Databricks) through a single unified platform

## License

See [LICENSE](LICENSE).
