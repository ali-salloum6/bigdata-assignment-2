#!/usr/bin/env python3
"""
Memgraph data loader for Big Data Assignment 2.
Creates nodes and relationships using the neo4j Python driver (bolt protocol).
"""

import os
import pandas as pd
from neo4j import GraphDatabase

CLEAN_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned')
BOLT_URI = 'bolt://localhost:7687'
BATCH_SIZE = 5000


def get_driver():
    return GraphDatabase.driver(BOLT_URI, auth=None)


def clear_db(driver):
    print("[Memgraph] Clearing database...")
    with driver.session() as s:
        s.run("MATCH (n) DETACH DELETE n")


def create_indexes(driver):
    print("[Memgraph] Creating indexes...")
    indexes = [
        "CREATE INDEX ON :User(user_id)",
        "CREATE INDEX ON :Product(product_id)",
        "CREATE INDEX ON :Campaign(campaign_id, campaign_type)",
        "CREATE INDEX ON :Category(category_code)",
    ]
    with driver.session() as s:
        for idx in indexes:
            try:
                s.run(idx)
            except Exception as e:
                print(f"  index note: {e}")


def batch_execute(driver, query, data, desc=""):
    total = len(data)
    for i in range(0, total, BATCH_SIZE):
        batch = data[i:i + BATCH_SIZE]
        with driver.session() as s:
            s.run(query, rows=batch)
        print(f"    {desc}: {min(i + BATCH_SIZE, total)}/{total}")


def load_users(driver):
    print("[Memgraph] Loading User nodes...")
    events = pd.read_csv(os.path.join(CLEAN_DIR, 'events.csv'), usecols=['user_id'])
    friends = pd.read_csv(os.path.join(CLEAN_DIR, 'friends.csv'))
    cfp = pd.read_csv(os.path.join(CLEAN_DIR, 'client_first_purchase_date.csv'), usecols=['user_id'])

    all_users = set(events['user_id'].unique())
    all_users.update(friends['friend1'].unique())
    all_users.update(friends['friend2'].unique())
    all_users.update(cfp['user_id'].unique())

    rows = [{'user_id': int(uid)} for uid in all_users]
    batch_execute(driver,
        "UNWIND $rows AS row MERGE (u:User {user_id: row.user_id})",
        rows, "users")
    print(f"  Total unique users: {len(rows)}")


def load_products(driver):
    print("[Memgraph] Loading Product and Category nodes...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, 'events.csv'),
                     usecols=['product_id', 'category_id', 'category_code', 'brand'])
    products = df.drop_duplicates(subset=['product_id']).fillna('')

    rows = products.to_dict('records')
    for r in rows:
        r['product_id'] = int(r['product_id'])
        r['category_id'] = int(r['category_id']) if r['category_id'] else 0

    batch_execute(driver, """
        UNWIND $rows AS row
        MERGE (p:Product {product_id: row.product_id})
        SET p.brand = row.brand, p.category_id = row.category_id
        WITH p, row
        WHERE row.category_code <> ''
        MERGE (c:Category {category_code: row.category_code})
        MERGE (p)-[:IN_CATEGORY]->(c)
    """, rows, "products")
    print(f"  Total unique products: {len(rows)}")


def load_campaigns(driver):
    print("[Memgraph] Loading Campaign nodes...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, 'campaigns.csv'))
    rows = df.to_dict('records')
    for r in rows:
        r['id'] = int(r['id'])

    batch_execute(driver, """
        UNWIND $rows AS row
        MERGE (c:Campaign {campaign_id: row.id, campaign_type: row.campaign_type})
        SET c.channel = row.channel,
            c.topic = row.topic,
            c.total_count = row.total_count,
            c.subject_length = row.subject_length
    """, rows, "campaigns")
    print(f"  Total campaigns: {len(rows)}")


def load_events(driver):
    print("[Memgraph] Loading PERFORMED relationships (events)...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, 'events.csv'),
                     usecols=['user_id', 'product_id', 'event_type', 'event_time', 'price', 'user_session'])

    rows = df.to_dict('records')
    for r in rows:
        r['user_id'] = int(r['user_id'])
        r['product_id'] = int(r['product_id'])
        r['price'] = float(r['price']) if r['price'] else 0.0

    batch_execute(driver, """
        UNWIND $rows AS row
        MATCH (u:User {user_id: row.user_id})
        MATCH (p:Product {product_id: row.product_id})
        CREATE (u)-[:PERFORMED {
            event_type: row.event_type,
            event_time: row.event_time,
            price: row.price,
            user_session: row.user_session
        }]->(p)
    """, rows, "events")
    print(f"  Total event edges: {len(rows)}")


def load_friends(driver):
    print("[Memgraph] Loading FRIENDS_WITH relationships...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, 'friends.csv'))
    rows = [{'f1': int(r['friend1']), 'f2': int(r['friend2'])} for _, r in df.iterrows()]

    batch_execute(driver, """
        UNWIND $rows AS row
        MATCH (a:User {user_id: row.f1})
        MATCH (b:User {user_id: row.f2})
        CREATE (a)-[:FRIENDS_WITH]->(b)
    """, rows, "friends")
    print(f"  Total friendship edges: {len(rows)}")


def load_messages(driver):
    print("[Memgraph] Loading Message nodes and relationships...")
    cols = ['id', 'campaign_id', 'message_type', 'client_id', 'channel',
            'is_opened', 'is_clicked', 'is_purchased', 'sent_at', 'user_id']
    df = pd.read_csv(os.path.join(CLEAN_DIR, 'messages.csv'), usecols=cols, low_memory=False)
    df = df.fillna('')

    rows = df.to_dict('records')
    for r in rows:
        r['id'] = int(r['id'])
        r['campaign_id'] = int(r['campaign_id']) if r['campaign_id'] != '' else 0
        r['client_id'] = int(r['client_id']) if r['client_id'] != '' else 0
        r['user_id'] = int(r['user_id']) if r['user_id'] != '' else 0

    batch_execute(driver, """
        UNWIND $rows AS row
        CREATE (m:Message {
            message_id: row.id,
            channel: row.channel,
            is_opened: row.is_opened,
            is_clicked: row.is_clicked,
            is_purchased: row.is_purchased,
            sent_at: row.sent_at
        })
        WITH m, row
        MATCH (u:User {user_id: row.user_id})
        CREATE (u)-[:RECEIVED]->(m)
        WITH m, row
        MATCH (c:Campaign {campaign_id: row.campaign_id, campaign_type: row.message_type})
        CREATE (m)-[:BELONGS_TO]->(c)
    """, rows, "messages")
    print(f"  Total messages: {len(rows)}")


def load_first_purchase(driver):
    print("[Memgraph] Loading first purchase data...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, 'client_first_purchase_date.csv'))
    rows = df.to_dict('records')
    for r in rows:
        r['user_id'] = int(r['user_id'])

    batch_execute(driver, """
        UNWIND $rows AS row
        MATCH (u:User {user_id: row.user_id})
        SET u.first_purchase_date = row.first_purchase_date,
            u.client_id = row.client_id
    """, rows, "first_purchase")


def main():
    driver = get_driver()
    clear_db(driver)
    create_indexes(driver)
    load_users(driver)
    load_products(driver)
    load_campaigns(driver)
    load_events(driver)
    load_friends(driver)
    load_messages(driver)
    load_first_purchase(driver)

    with driver.session() as s:
        result = s.run("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt")
        print("\n[Memgraph] Node counts:")
        for r in result:
            print(f"  {r['label']}: {r['cnt']}")

        result = s.run("MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS cnt")
        print("[Memgraph] Relationship counts:")
        for r in result:
            print(f"  {r['type']}: {r['cnt']}")

    driver.close()
    print("[Memgraph] Done.")


if __name__ == '__main__':
    main()
