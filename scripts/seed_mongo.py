"""Seed a MongoDB collection with the CSV data in data/sales_sample.csv.

Usage:
  - make sure pymongo is installed (requirements.txt includes it)
  - set MONGO_URI environment variable (e.g. mongodb://localhost:27017/)
  - optionally set MONGO_DB and MONGO_COLLECTION, defaults are sales_db and sales
  - run: python scripts/seed_mongo.py
"""

import os
import pandas as pd


def main():
    uri = os.environ.get("MONGO_URI")
    if not uri:
        raise SystemExit(
            "MONGO_URI not set. Example: export MONGO_URI='mongodb://localhost:27017/'"
        )

    mongo_db = os.environ.get("MONGO_DB", "sales_db")
    mongo_coll = os.environ.get("MONGO_COLLECTION", "sales")

    try:
        from pymongo import MongoClient
    except Exception as e:
        raise SystemExit("pymongo not available. Install requirements.txt") from e

    client = MongoClient(uri)
    db = client[mongo_db]
    coll = db[mongo_coll]

    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "sales_sample.csv")
    df = pd.read_csv(csv_path)

    # Convert to list of dicts and insert
    docs = df.to_dict(orient="records")

    # optional: clear collection first
    print(
        f"Seeding collection '{mongo_db}.{mongo_coll}' — dropping existing documents first..."
    )
    coll.delete_many({})
    result = coll.insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} documents")


if __name__ == "__main__":
    main()
