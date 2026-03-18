#!/usr/bin/env python3
"""
PostgreSQL data loader for Big Data Assignment 2.
Creates tables and bulk-loads cleaned CSVs using COPY.
"""

import os
import psycopg2

CLEAN_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned')

CONN_PARAMS = dict(
    host='localhost', port=5432,
    user='bigdata', password='bigdata',
    dbname='ecommerce'
)

DDL = """
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;
DROP TABLE IF EXISTS friends CASCADE;
DROP TABLE IF EXISTS client_first_purchase CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE campaigns (
    id              INTEGER NOT NULL,
    campaign_type   VARCHAR(50) NOT NULL,
    channel         VARCHAR(50) NOT NULL,
    topic           TEXT,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    total_count     INTEGER DEFAULT 0,
    ab_test         BOOLEAN DEFAULT FALSE,
    warmup_mode     BOOLEAN DEFAULT FALSE,
    hour_limit      INTEGER DEFAULT 0,
    subject_length  REAL DEFAULT 0,
    subject_with_personalization BOOLEAN DEFAULT FALSE,
    subject_with_deadline        BOOLEAN DEFAULT FALSE,
    subject_with_emoji           BOOLEAN DEFAULT FALSE,
    subject_with_bonuses         BOOLEAN DEFAULT FALSE,
    subject_with_discount        BOOLEAN DEFAULT FALSE,
    subject_with_saleout         BOOLEAN DEFAULT FALSE,
    is_test         BOOLEAN DEFAULT FALSE,
    position        INTEGER DEFAULT 0,
    PRIMARY KEY (id, campaign_type)
);

CREATE TABLE events (
    event_time      TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type      VARCHAR(20) NOT NULL,
    product_id      BIGINT NOT NULL,
    category_id     BIGINT,
    category_code   TEXT,
    brand           TEXT,
    price           NUMERIC(12,2),
    user_id         BIGINT NOT NULL,
    user_session    UUID
);

CREATE TABLE messages (
    id                      BIGINT PRIMARY KEY,
    message_id              TEXT,
    campaign_id             INTEGER,
    message_type            VARCHAR(50),
    client_id               BIGINT,
    channel                 VARCHAR(50),
    category                TEXT,
    platform                TEXT,
    email_provider          TEXT,
    stream                  TEXT,
    date                    DATE,
    sent_at                 TIMESTAMP,
    is_opened               BOOLEAN DEFAULT FALSE,
    opened_first_time_at    TIMESTAMP,
    opened_last_time_at     TIMESTAMP,
    is_clicked              BOOLEAN DEFAULT FALSE,
    clicked_first_time_at   TIMESTAMP,
    clicked_last_time_at    TIMESTAMP,
    is_unsubscribed         BOOLEAN DEFAULT FALSE,
    unsubscribed_at         TIMESTAMP,
    is_hard_bounced         BOOLEAN DEFAULT FALSE,
    hard_bounced_at         TIMESTAMP,
    is_soft_bounced         BOOLEAN DEFAULT FALSE,
    soft_bounced_at         TIMESTAMP,
    is_complained           BOOLEAN DEFAULT FALSE,
    complained_at           TIMESTAMP,
    is_blocked              BOOLEAN DEFAULT FALSE,
    blocked_at              TIMESTAMP,
    is_purchased            BOOLEAN DEFAULT FALSE,
    purchased_at            TIMESTAMP,
    created_at              TIMESTAMP,
    updated_at              TIMESTAMP,
    user_device_id          BIGINT,
    user_id                 BIGINT
);

CREATE TABLE client_first_purchase (
    client_id           BIGINT PRIMARY KEY,
    first_purchase_date DATE,
    user_id             BIGINT,
    user_device_id      BIGINT
);

CREATE TABLE friends (
    friend1 BIGINT NOT NULL,
    friend2 BIGINT NOT NULL
);
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_product_id ON events(product_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_messages_client_id ON messages(client_id);
CREATE INDEX IF NOT EXISTS idx_messages_campaign ON messages(campaign_id, message_type);
CREATE INDEX IF NOT EXISTS idx_messages_purchased ON messages(is_purchased) WHERE is_purchased = TRUE;
CREATE INDEX IF NOT EXISTS idx_friends_1 ON friends(friend1);
CREATE INDEX IF NOT EXISTS idx_friends_2 ON friends(friend2);
CREATE INDEX IF NOT EXISTS idx_cfp_user ON client_first_purchase(user_id);
"""


def copy_csv(cur, table, filename, columns=None):
    path = os.path.join(CLEAN_DIR, filename)
    print(f"  COPY {table} from {filename}...")
    col_clause = f"({', '.join(columns)})" if columns else ""
    with open(path, 'r') as f:
        cur.copy_expert(
            f"COPY {table} {col_clause} FROM STDIN WITH CSV HEADER NULL ''",
            f
        )


def main():
    conn = psycopg2.connect(**CONN_PARAMS)
    conn.autocommit = True
    cur = conn.cursor()

    print("[PSQL] Creating tables...")
    cur.execute(DDL)

    print("[PSQL] Loading data...")
    copy_csv(cur, 'campaigns', 'campaigns.csv')
    copy_csv(cur, 'events', 'events.csv')
    copy_csv(cur, 'messages', 'messages.csv')
    copy_csv(cur, 'client_first_purchase', 'client_first_purchase_date.csv')
    copy_csv(cur, 'friends', 'friends.csv')

    print("[PSQL] Creating indexes...")
    cur.execute(INDEXES)

    cur.execute("SELECT COUNT(*) FROM events")
    print(f"  events: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM campaigns")
    print(f"  campaigns: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM messages")
    print(f"  messages: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM friends")
    print(f"  friends: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM client_first_purchase")
    print(f"  client_first_purchase: {cur.fetchone()[0]}")

    cur.close()
    conn.close()
    print("[PSQL] Done.")


if __name__ == '__main__':
    main()
