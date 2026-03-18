#!/usr/bin/env python3
"""
MongoDB data loader for Big Data Assignment 2.
Creates collections and loads cleaned CSVs using pymongo.
"""

import os
import math
import pandas as pd
from pymongo import MongoClient, ASCENDING, TEXT

CLEAN_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned')
BATCH_SIZE = 10000


def nan_to_none(record):
    """Replace NaN/NaT with None for MongoDB."""
    return {
        k: (None if (isinstance(v, float) and math.isnan(v)) else v)
        for k, v in record.items()
    }


def load_collection(db, name, filename, indexes=None, chunk_size=50000):
    path = os.path.join(CLEAN_DIR, filename)
    print(f"  Loading {name} from {filename}...")
    db.drop_collection(name)
    coll = db[name]

    total = 0
    for chunk in pd.read_csv(path, chunksize=chunk_size, low_memory=False):
        records = chunk.to_dict('records')
        records = [nan_to_none(r) for r in records]
        for i in range(0, len(records), BATCH_SIZE):
            coll.insert_many(records[i:i + BATCH_SIZE])
        total += len(records)
        print(f"    {total} rows inserted...")

    if indexes:
        for idx in indexes:
            coll.create_index(idx)
            print(f"    index created: {idx}")

    print(f"  {name}: {coll.count_documents({})} docs")
    return coll


def main():
    client = MongoClient('localhost', 27017)
    db = client['ecommerce']

    print("[MongoDB] Loading data...")

    load_collection(db, 'events', 'events.csv', indexes=[
        [('user_id', ASCENDING)],
        [('product_id', ASCENDING)],
        [('event_type', ASCENDING)],
        [('category_code', TEXT)],
    ])

    load_collection(db, 'campaigns', 'campaigns.csv', indexes=[
        [('id', ASCENDING), ('campaign_type', ASCENDING)],
    ])

    load_collection(db, 'messages', 'messages.csv', indexes=[
        [('client_id', ASCENDING)],
        [('campaign_id', ASCENDING), ('message_type', ASCENDING)],
        [('is_purchased', ASCENDING)],
    ])

    load_collection(db, 'client_first_purchase', 'client_first_purchase_date.csv', indexes=[
        [('client_id', ASCENDING)],
        [('user_id', ASCENDING)],
    ])

    load_collection(db, 'friends', 'friends.csv', indexes=[
        [('friend1', ASCENDING)],
        [('friend2', ASCENDING)],
    ])

    client.close()
    print("[MongoDB] Done.")


if __name__ == '__main__':
    main()
