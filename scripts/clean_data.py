#!/usr/bin/env python3
"""
Data cleaning script for Big Data Assignment 2.
Reads raw CSVs from data/raw/, cleans and normalizes them,
writes cleaned CSVs to data/cleaned/.
"""

import os
import pandas as pd
import numpy as np

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
CLEAN_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned')
os.makedirs(CLEAN_DIR, exist_ok=True)


def clean_events():
    print("[events] Loading...")
    df = pd.read_csv(os.path.join(RAW_DIR, 'events.csv'))
    print(f"  raw rows: {len(df)}")

    df['event_time'] = pd.to_datetime(df['event_time'], format='%Y-%m-%d %H:%M:%S UTC', utc=True)
    df['category_code'] = df['category_code'].fillna('')
    df['brand'] = df['brand'].fillna('')

    df = df.drop_duplicates()
    print(f"  cleaned rows: {len(df)}")

    out = os.path.join(CLEAN_DIR, 'events.csv')
    df.to_csv(out, index=False)
    print(f"  -> {out}")
    return df


def clean_campaigns():
    print("[campaigns] Loading...")
    df = pd.read_csv(os.path.join(RAW_DIR, 'campaigns.csv'))
    print(f"  raw rows: {len(df)}")

    df['started_at'] = pd.to_datetime(df['started_at'], errors='coerce')
    df['finished_at'] = pd.to_datetime(df['finished_at'], errors='coerce')
    df['topic'] = df['topic'].fillna('')

    bool_cols = [
        'warmup_mode', 'subject_with_personalization', 'subject_with_deadline',
        'subject_with_emoji', 'subject_with_bonuses', 'subject_with_discount',
        'subject_with_saleout'
    ]
    for col in bool_cols:
        df[col] = df[col].astype(bool)

    df['ab_test'] = df['ab_test'].fillna(False).astype(bool)
    df['is_test'] = df['is_test'].fillna(False).astype(bool)
    df['hour_limit'] = df['hour_limit'].fillna(0).astype(int)
    df['position'] = df['position'].fillna(0).astype(int)
    df['total_count'] = df['total_count'].fillna(0).astype(int)
    df['subject_length'] = df['subject_length'].fillna(0.0)

    df = df.drop_duplicates()
    print(f"  cleaned rows: {len(df)}")

    out = os.path.join(CLEAN_DIR, 'campaigns.csv')
    df.to_csv(out, index=False)
    print(f"  -> {out}")
    return df


def clean_messages():
    print("[messages] Loading...")
    df = pd.read_csv(os.path.join(RAW_DIR, 'messages.csv'), low_memory=False)
    print(f"  raw rows: {len(df)}")

    bool_map = {'t': True, 'f': False, True: True, False: False}
    bool_cols = [
        'is_opened', 'is_clicked', 'is_unsubscribed',
        'is_hard_bounced', 'is_soft_bounced', 'is_complained',
        'is_blocked', 'is_purchased'
    ]
    for col in bool_cols:
        df[col] = df[col].map(bool_map).fillna(False).astype(bool)

    dt_cols = [
        'sent_at', 'opened_first_time_at', 'opened_last_time_at',
        'clicked_first_time_at', 'clicked_last_time_at',
        'unsubscribed_at', 'hard_bounced_at', 'soft_bounced_at',
        'complained_at', 'blocked_at', 'purchased_at',
        'created_at', 'updated_at'
    ]
    for col in dt_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date

    df['email_provider'] = df['email_provider'].fillna('')
    df['platform'] = df['platform'].fillna('').astype(str)
    df['stream'] = df['stream'].fillna('').astype(str)
    df['category'] = df['category'].fillna('').astype(str)

    df = df.drop_duplicates()
    print(f"  cleaned rows: {len(df)}")

    out = os.path.join(CLEAN_DIR, 'messages.csv')
    df.to_csv(out, index=False)
    print(f"  -> {out}")
    return df


def clean_client_first_purchase():
    print("[client_first_purchase_date] Loading...")
    df = pd.read_csv(os.path.join(RAW_DIR, 'client_first_purchase_date.csv'))
    print(f"  raw rows: {len(df)}")

    df['first_purchase_date'] = pd.to_datetime(df['first_purchase_date'], errors='coerce').dt.date

    df = df.drop_duplicates()
    print(f"  cleaned rows: {len(df)}")

    out = os.path.join(CLEAN_DIR, 'client_first_purchase_date.csv')
    df.to_csv(out, index=False)
    print(f"  -> {out}")
    return df


def clean_friends():
    print("[friends] Loading...")
    df = pd.read_csv(os.path.join(RAW_DIR, 'friends.csv'))
    print(f"  raw rows: {len(df)}")

    df = df.drop_duplicates()
    df = df.dropna()
    df['friend1'] = df['friend1'].astype(np.int64)
    df['friend2'] = df['friend2'].astype(np.int64)
    print(f"  cleaned rows: {len(df)}")

    out = os.path.join(CLEAN_DIR, 'friends.csv')
    df.to_csv(out, index=False)
    print(f"  -> {out}")
    return df


if __name__ == '__main__':
    clean_events()
    clean_campaigns()
    clean_messages()
    clean_client_first_purchase()
    clean_friends()
    print("\nAll datasets cleaned successfully.")
