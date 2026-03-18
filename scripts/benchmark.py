#!/usr/bin/env python3
"""
Benchmarking script for Big Data Assignment 2.
Runs each query 5 times per database, collects timing data,
computes stats, and generates charts.
"""

import os
import csv
import time
import json
import statistics
import psycopg2
import psycopg2.extras
from pymongo import MongoClient
from neo4j import GraphDatabase
import matplotlib.pyplot as plt
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

PSQL_CONN = dict(host='localhost', port=5432, user='bigdata', password='bigdata', dbname='ecommerce')
MONGO_URI = 'mongodb://localhost:27017'
BOLT_URI = 'bolt://localhost:7687'

RUNS = 5

# ─── Query definitions ────────────────────────────────────────────────────────

Q1_PSQL = """
SELECT c.campaign_type, c.channel,
    COUNT(m.id) AS total_messages,
    SUM(CASE WHEN m.is_purchased THEN 1 ELSE 0 END) AS purchases,
    ROUND(100.0 * SUM(CASE WHEN m.is_purchased THEN 1 ELSE 0 END) / NULLIF(COUNT(m.id), 0), 2) AS purchase_rate_pct
FROM messages m
JOIN campaigns c ON c.id = m.campaign_id AND c.campaign_type = m.message_type
GROUP BY c.campaign_type, c.channel
ORDER BY purchase_rate_pct DESC;
"""

Q2_PSQL = """
SELECT product_id, category_code, brand,
    SUM(CASE event_type WHEN 'purchase' THEN 5 WHEN 'cart' THEN 3 WHEN 'view' THEN 1 ELSE 0 END) AS total_score,
    COUNT(DISTINCT user_id) AS unique_users
FROM events WHERE category_code != ''
GROUP BY product_id, category_code, brand
ORDER BY total_score DESC LIMIT 20;
"""

Q3_PSQL = """
SELECT DISTINCT product_id, category_code, brand, price
FROM events
WHERE to_tsvector('english', REPLACE(category_code, '.', ' ')) @@ to_tsquery('english', 'electronics')
ORDER BY product_id LIMIT 20;
"""

Q1_MONGO = [
    {"$group": {
        "_id": {"message_type": "$message_type", "channel": "$channel"},
        "total_messages": {"$sum": 1},
        "purchases": {"$sum": {"$cond": ["$is_purchased", 1, 0]}}
    }},
    {"$addFields": {
        "purchase_rate_pct": {"$round": [{"$multiply": [{"$divide": ["$purchases", "$total_messages"]}, 100]}, 2]}
    }},
    {"$sort": {"purchase_rate_pct": -1}}
]

Q2_MONGO = [
    {"$match": {"category_code": {"$ne": ""}}},
    {"$group": {"_id": {"product_id": "$product_id", "category_code": "$category_code", "brand": "$brand"},
                "total_score": {"$sum": {"$switch": {"branches": [
                    {"case": {"$eq": ["$event_type", "purchase"]}, "then": 5},
                    {"case": {"$eq": ["$event_type", "cart"]}, "then": 3},
                    {"case": {"$eq": ["$event_type", "view"]}, "then": 1}
                ], "default": 0}}},
                "unique_users": {"$addToSet": "$user_id"}}},
    {"$addFields": {"unique_users_count": {"$size": "$unique_users"}}},
    {"$sort": {"total_score": -1}}, {"$limit": 20}
]

Q3_MONGO = [
    {"$match": {"$text": {"$search": "electronics"}}},
    {"$project": {"product_id": 1, "category_code": 1, "brand": 1, "price": 1, "_id": 0,
                  "score": {"$meta": "textScore"}}},
    {"$sort": {"score": {"$meta": "textScore"}}},
    {"$limit": 20}
]

Q1_CYPHER = """
MATCH (u:User)-[:RECEIVED]->(m:Message)-[:BELONGS_TO]->(c:Campaign)
WITH c.campaign_type AS campaign_type, c.channel AS channel,
     COUNT(m) AS total_messages,
     SUM(CASE WHEN m.is_purchased = true THEN 1 ELSE 0 END) AS purchases
RETURN campaign_type, channel, total_messages, purchases,
       toFloat(toInteger(10000.0 * purchases / total_messages)) / 100.0 AS purchase_rate_pct
ORDER BY purchase_rate_pct DESC
"""

Q2_CYPHER = """
MATCH (u:User)-[r:PERFORMED]->(p:Product)-[:IN_CATEGORY]->(c:Category)
WITH p, c,
     SUM(CASE r.event_type WHEN 'purchase' THEN 5 WHEN 'cart' THEN 3 WHEN 'view' THEN 1 ELSE 0 END) AS total_score,
     COUNT(DISTINCT u) AS unique_users
RETURN p.product_id AS product_id, c.category_code AS category_code, p.brand AS brand,
       total_score, unique_users
ORDER BY total_score DESC LIMIT 20
"""

Q3_CYPHER = """
MATCH (p:Product)-[:IN_CATEGORY]->(c:Category)
WHERE c.category_code CONTAINS 'electronics'
RETURN DISTINCT p.product_id AS product_id, c.category_code AS category_code, p.brand AS brand
ORDER BY product_id LIMIT 20
"""


def bench_psql(query, runs=RUNS):
    times = []
    for i in range(runs):
        conn = psycopg2.connect(**PSQL_CONN)
        cur = conn.cursor()
        start = time.perf_counter()
        cur.execute(query)
        cur.fetchall()
        elapsed = time.perf_counter() - start
        cur.close()
        conn.close()
        times.append(elapsed)
        print(f"    run {i+1}: {elapsed:.4f}s")
    return times


def bench_mongo(collection, pipeline, runs=RUNS):
    times = []
    for i in range(runs):
        client = MongoClient(MONGO_URI)
        db = client['ecommerce']
        start = time.perf_counter()
        list(db[collection].aggregate(pipeline, allowDiskUse=True))
        elapsed = time.perf_counter() - start
        client.close()
        times.append(elapsed)
        print(f"    run {i+1}: {elapsed:.4f}s")
    return times


def bench_cypher(query, runs=RUNS):
    times = []
    for i in range(runs):
        driver = GraphDatabase.driver(BOLT_URI, auth=None)
        start = time.perf_counter()
        with driver.session() as s:
            list(s.run(query))
        elapsed = time.perf_counter() - start
        driver.close()
        times.append(elapsed)
        print(f"    run {i+1}: {elapsed:.4f}s")
    return times


def main():
    results = []

    test_cases = [
        ("Q1", "Campaign effectiveness",
         Q1_PSQL, "messages", Q1_MONGO, Q1_CYPHER),
        ("Q2", "Product recommendations",
         Q2_PSQL, "events", Q2_MONGO, Q2_CYPHER),
        ("Q3", "Full-text search",
         Q3_PSQL, "events", Q3_MONGO, Q3_CYPHER),
    ]

    for qid, desc, psql_q, mongo_coll, mongo_pipe, cypher_q in test_cases:
        print(f"\n{'='*50}")
        print(f"  Benchmarking {qid}: {desc}")
        print(f"{'='*50}")

        for db_name, bench_fn, args in [
            ("PostgreSQL", bench_psql, (psql_q,)),
            ("MongoDB", bench_mongo, (mongo_coll, mongo_pipe)),
            ("Memgraph", bench_cypher, (cypher_q,)),
        ]:
            print(f"\n  [{db_name}]")
            try:
                times = bench_fn(*args)
                mean_t = statistics.mean(times)
                std_t = statistics.stdev(times) if len(times) > 1 else 0
                results.append({
                    "query": qid,
                    "database": db_name,
                    "times": times,
                    "mean": mean_t,
                    "std": std_t
                })
                print(f"  => Mean: {mean_t:.4f}s, Std: {std_t:.4f}s")
            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({
                    "query": qid,
                    "database": db_name,
                    "times": [],
                    "mean": 0,
                    "std": 0,
                    "error": str(e)
                })

    # Save raw results
    csv_path = os.path.join(OUTPUT_DIR, 'benchmark_results.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['query', 'database', 'run1', 'run2', 'run3', 'run4', 'run5', 'mean', 'std'])
        for r in results:
            times = r['times'] + [0] * (5 - len(r['times']))
            writer.writerow([r['query'], r['database']] + [f"{t:.4f}" for t in times] + [f"{r['mean']:.4f}", f"{r['std']:.4f}"])
    print(f"\nResults saved to {csv_path}")

    json_path = os.path.join(OUTPUT_DIR, 'benchmark_results.json')
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Generate chart
    generate_chart(results)


def generate_chart(results):
    queries = sorted(set(r['query'] for r in results))
    databases = ['PostgreSQL', 'MongoDB', 'Memgraph']
    colors = ['#2196F3', '#4CAF50', '#FF9800']

    x = np.arange(len(queries))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, db_name in enumerate(databases):
        means = []
        stds = []
        for q in queries:
            match = [r for r in results if r['query'] == q and r['database'] == db_name]
            if match:
                means.append(match[0]['mean'])
                stds.append(match[0]['std'])
            else:
                means.append(0)
                stds.append(0)
        bars = ax.bar(x + i * width, means, width, yerr=stds, label=db_name,
                      color=colors[i], capsize=4, alpha=0.85)
        for bar, mean in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                    f'{mean:.3f}s', ha='center', va='bottom', fontsize=8)

    ax.set_xlabel('Query')
    ax.set_ylabel('Execution Time (seconds)')
    ax.set_title('Query Execution Times — PostgreSQL vs MongoDB vs Memgraph')
    ax.set_xticks(x + width)
    ax.set_xticklabels(queries)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    chart_path = os.path.join(OUTPUT_DIR, 'benchmark_chart.png')
    plt.savefig(chart_path, dpi=150)
    print(f"Chart saved to {chart_path}")
    plt.close()


if __name__ == '__main__':
    main()
