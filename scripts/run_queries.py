#!/usr/bin/env python3
"""
Query runner for Big Data Assignment 2.
Runs Q1, Q2, Q3 against PostgreSQL, MongoDB, and Memgraph.
Prints results and saves to output/.
"""

import os
import json
import time
import psycopg2
import psycopg2.extras
from pymongo import MongoClient
from neo4j import GraphDatabase

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

PSQL_CONN = dict(host='localhost', port=5432, user='bigdata', password='bigdata', dbname='ecommerce')
MONGO_URI = 'mongodb://localhost:27017'
BOLT_URI = 'bolt://localhost:7687'


def run_psql_query(query, desc=""):
    conn = psycopg2.connect(**PSQL_CONN)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    start = time.perf_counter()
    cur.execute(query)
    rows = cur.fetchall()
    elapsed = time.perf_counter() - start
    cur.close()
    conn.close()
    return [dict(r) for r in rows], elapsed


def run_mongo_pipeline(collection, pipeline, desc=""):
    client = MongoClient(MONGO_URI)
    db = client['ecommerce']
    start = time.perf_counter()
    results = list(db[collection].aggregate(pipeline, allowDiskUse=True))
    elapsed = time.perf_counter() - start
    client.close()
    for r in results:
        if '_id' in r:
            r['_id'] = str(r['_id'])
    return results, elapsed


def run_cypher_query(query, desc=""):
    driver = GraphDatabase.driver(BOLT_URI, auth=None)
    start = time.perf_counter()
    with driver.session() as session:
        result = session.run(query)
        rows = [dict(r) for r in result]
    elapsed = time.perf_counter() - start
    driver.close()
    return rows, elapsed


def save_results(name, results):
    path = os.path.join(OUTPUT_DIR, f'{name}.json')
    with open(path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"  Saved to {path}")


# ─── Q1: Campaign effectiveness ──────────────────────────────────────────────

Q1_PSQL = """
SELECT
    c.campaign_type, c.channel,
    COUNT(m.id) AS total_messages,
    SUM(CASE WHEN m.is_purchased THEN 1 ELSE 0 END) AS purchases,
    ROUND(100.0 * SUM(CASE WHEN m.is_purchased THEN 1 ELSE 0 END) / NULLIF(COUNT(m.id), 0), 2) AS purchase_rate_pct
FROM messages m
JOIN campaigns c ON c.id = m.campaign_id AND c.campaign_type = m.message_type
GROUP BY c.campaign_type, c.channel
ORDER BY purchase_rate_pct DESC;
"""

Q1_MONGO_PIPELINE = [
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

Q1_CYPHER = """
MATCH (u:User)-[:RECEIVED]->(m:Message)-[:BELONGS_TO]->(c:Campaign)
WITH c.campaign_type AS campaign_type, c.channel AS channel,
     COUNT(m) AS total_messages,
     SUM(CASE WHEN m.is_purchased = true THEN 1 ELSE 0 END) AS purchases
RETURN campaign_type, channel, total_messages, purchases,
       toFloat(toInteger(10000.0 * purchases / total_messages)) / 100.0 AS purchase_rate_pct
ORDER BY purchase_rate_pct DESC
"""

# ─── Q2: Product recommendations ─────────────────────────────────────────────

Q2_PSQL = """
SELECT product_id, category_code, brand,
    SUM(CASE event_type WHEN 'purchase' THEN 5 WHEN 'cart' THEN 3 WHEN 'view' THEN 1 ELSE 0 END) AS total_score,
    COUNT(DISTINCT user_id) AS unique_users
FROM events
WHERE category_code != ''
GROUP BY product_id, category_code, brand
ORDER BY total_score DESC
LIMIT 20;
"""

Q2_MONGO_PIPELINE = [
    {"$match": {"category_code": {"$ne": ""}}},
    {"$group": {
        "_id": {"product_id": "$product_id", "category_code": "$category_code", "brand": "$brand"},
        "total_score": {"$sum": {"$switch": {
            "branches": [
                {"case": {"$eq": ["$event_type", "purchase"]}, "then": 5},
                {"case": {"$eq": ["$event_type", "cart"]}, "then": 3},
                {"case": {"$eq": ["$event_type", "view"]}, "then": 1}
            ],
            "default": 0
        }}},
        "unique_users": {"$addToSet": "$user_id"}
    }},
    {"$addFields": {"unique_users_count": {"$size": "$unique_users"}}},
    {"$sort": {"total_score": -1}},
    {"$limit": 20},
    {"$project": {
        "_id": 0, "product_id": "$_id.product_id",
        "category_code": "$_id.category_code", "brand": "$_id.brand",
        "total_score": 1, "unique_users": "$unique_users_count"
    }}
]

Q2_CYPHER = """
MATCH (u:User)-[r:PERFORMED]->(p:Product)-[:IN_CATEGORY]->(c:Category)
WITH p, c,
     SUM(CASE r.event_type WHEN 'purchase' THEN 5 WHEN 'cart' THEN 3 WHEN 'view' THEN 1 ELSE 0 END) AS total_score,
     COUNT(DISTINCT u) AS unique_users
RETURN p.product_id AS product_id, c.category_code AS category_code, p.brand AS brand,
       total_score, unique_users
ORDER BY total_score DESC
LIMIT 20
"""

# ─── Q3: Full-text search ────────────────────────────────────────────────────

Q3_PSQL = """
CREATE INDEX IF NOT EXISTS idx_events_fts_category
ON events USING GIN (to_tsvector('english', REPLACE(category_code, '.', ' ')));

SELECT DISTINCT product_id, category_code, brand, price
FROM events
WHERE to_tsvector('english', REPLACE(category_code, '.', ' ')) @@ to_tsquery('english', 'electronics')
ORDER BY product_id
LIMIT 20;
"""

Q3_MONGO_PIPELINE = [
    {"$match": {"$text": {"$search": "electronics"}}},
    {"$project": {"product_id": 1, "category_code": 1, "brand": 1, "price": 1, "_id": 0, "score": {"$meta": "textScore"}}},
    {"$sort": {"score": {"$meta": "textScore"}}},
    {"$limit": 20}
]

Q3_CYPHER = """
MATCH (p:Product)-[:IN_CATEGORY]->(c:Category)
WHERE c.category_code CONTAINS 'electronics'
RETURN DISTINCT p.product_id AS product_id, c.category_code AS category_code, p.brand AS brand
ORDER BY product_id
LIMIT 20
"""


def main():
    all_results = {}

    queries = [
        ("q1", "Campaign effectiveness",
         Q1_PSQL, "messages", Q1_MONGO_PIPELINE, Q1_CYPHER),
        ("q2", "Product recommendations",
         Q2_PSQL, "events", Q2_MONGO_PIPELINE, Q2_CYPHER),
        ("q3", "Full-text search",
         Q3_PSQL, "events", Q3_MONGO_PIPELINE, Q3_CYPHER),
    ]

    for qid, desc, psql_q, mongo_coll, mongo_pipe, cypher_q in queries:
        print(f"\n{'='*60}")
        print(f"  {qid.upper()}: {desc}")
        print(f"{'='*60}")

        print(f"\n[PSQL] Running {qid}...")
        try:
            rows, t = run_psql_query(psql_q, desc)
            print(f"  Rows: {len(rows)}, Time: {t:.4f}s")
            for r in rows[:5]:
                print(f"    {r}")
            all_results[f"{qid}_psql"] = {"rows": len(rows), "time": t, "sample": rows[:5]}
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[f"{qid}_psql"] = {"error": str(e)}

        print(f"\n[MongoDB] Running {qid}...")
        try:
            rows, t = run_mongo_pipeline(mongo_coll, mongo_pipe, desc)
            print(f"  Rows: {len(rows)}, Time: {t:.4f}s")
            for r in rows[:5]:
                print(f"    {r}")
            all_results[f"{qid}_mongo"] = {"rows": len(rows), "time": t, "sample": rows[:5]}
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[f"{qid}_mongo"] = {"error": str(e)}

        print(f"\n[Memgraph] Running {qid}...")
        try:
            rows, t = run_cypher_query(cypher_q, desc)
            print(f"  Rows: {len(rows)}, Time: {t:.4f}s")
            for r in rows[:5]:
                print(f"    {r}")
            all_results[f"{qid}_memgraph"] = {"rows": len(rows), "time": t, "sample": rows[:5]}
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[f"{qid}_memgraph"] = {"error": str(e)}

    save_results("query_results", all_results)
    print("\nAll queries completed.")


if __name__ == '__main__':
    main()
