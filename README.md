# Big Data Assignment 2 (f29)

This repo contains **scripts + outputs** for the “Big Data Storage & Retrieval” assignment using:
- **PostgreSQL** (SQL)
- **MongoDB** (NoSQL document)
- **Memgraph** (graph, Neo4j-compatible Bolt)

Raw data is **not committed** (see `.gitignore`).

## Prerequisites

- Docker Desktop
- Python 3

## Quickstart

From the repo root:

```bash
docker compose up -d
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Data locations

- **Raw CSVs**: `data/raw/` (already prepared from `f29`)
- **Cleaned CSVs**: `data/cleaned/` (generated)

## Run pipeline

### 1) Clean data

```bash
source .venv/bin/activate
python3 scripts/clean_data.py
```

### 2) Load databases

```bash
./scripts/load_data_psql.sh
./scripts/load_data_mongodb.sh
./scripts/load_data_graph.sh
```

### 3) Run analysis queries

```bash
python3 scripts/run_queries.py
```

Outputs:
- `output/query_results.json`

### 4) Benchmark (5 runs/query/DB)

```bash
python3 -u scripts/benchmark.py
```

Outputs:
- `output/benchmark_results.csv`
- `output/benchmark_results.json`
- `output/benchmark_chart.png`

### 5) Generate report

```bash
python3 scripts/generate_report.py
```

Output:
- `report.pdf`

## Screenshots

- **Hackolade diagrams**: in `screenshots/` as:
  - `model_psql.png`, `model_mongodb.png`, `model_memgraph.png`
- **Query screenshots**: in `screenshots/` as:
  - `q1_psql.png`, `q1_mongo.png`, `q1_memgraph.png`
  - `q2_psql.png`, `q2_mongo.png`, `q2_memgraph.png`
  - `q3_psql.png`, `q3_mongo.png`, `q3_memgraph.png`
- `benchmark_chart.png` in `screenshots/`

## Services / Ports

- **PostgreSQL**: `localhost:5432` (user/pass/db: `bigdata` / `bigdata` / `ecommerce`)
- **MongoDB**: `localhost:27017` (db: `ecommerce`)
- **Memgraph (Bolt)**: `localhost:7687`
- **Memgraph Lab UI**: `http://localhost:3000`

