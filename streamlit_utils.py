import os
from pathlib import Path
from typing import Optional

import pandas as pd


DATA_PATH = Path(__file__).parent / "data" / "sales_sample.csv"


def ensure_datetime(df: pd.DataFrame) -> pd.DataFrame:
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"])
        df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
        df["year"] = df["order_date"].dt.year
    return df


def load_csv_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    return ensure_datetime(df)


def try_import_pymongo():
    try:
        import pymongo  # type: ignore

        return pymongo
    except Exception:
        return None


def get_mongo_client(uri: str):
    pymongo = try_import_pymongo()
    if not pymongo:
        return None
    from pymongo import MongoClient  # type: ignore

    try:
        client = MongoClient(uri)
        return client
    except Exception:
        return None


def load_mongo_collection(client, db_name: str, collection_name: str) -> pd.DataFrame:
    try:
        coll = client[db_name][collection_name]
        data = list(coll.find())
        df = pd.DataFrame(data)
        if "_id" in df.columns:
            try:
                df["_id"] = df["_id"].astype(str)
            except Exception:
                pass
        return ensure_datetime(df)
    except Exception:
        return pd.DataFrame()


def get_dataframe(
    source: str = "auto",
    mongo_uri: Optional[str] = None,
    mongo_db: Optional[str] = None,
    mongo_collection: Optional[str] = None,
) -> pd.DataFrame:
    if source == "csv":
        return load_csv_data()

    if mongo_uri and try_import_pymongo():
        client = get_mongo_client(mongo_uri)
        if client:
            db_name = mongo_db or os.environ.get("MONGO_DB", "sales_db")
            coll_name = mongo_collection or os.environ.get("MONGO_COLLECTION", "sales")
            df = load_mongo_collection(client, db_name, coll_name)
            if not df.empty:
                return df

    return load_csv_data()
