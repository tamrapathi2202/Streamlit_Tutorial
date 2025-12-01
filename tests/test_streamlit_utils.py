import os
import pandas as pd
from streamlit_utils import ensure_datetime, load_csv_data, get_dataframe


def test_ensure_datetime_adds_month_year():
    df = pd.DataFrame({"order_date": ["2024-01-01", "2024-02-15"]})
    out = ensure_datetime(df)
    assert "order_date" in out.columns
    assert pd.api.types.is_datetime64_any_dtype(out["order_date"])
    assert "month" in out.columns
    assert "year" in out.columns


def test_load_csv_data_reads_rows():
    df = load_csv_data()
    # file has 24 rows in sample dataset
    assert not df.empty
    assert "sales" in df.columns


def test_get_dataframe_csv_mode():
    # ensure we get the CSV when forcing csv mode
    df = get_dataframe(source="csv")
    assert not df.empty
    # auto should default to csv when no MONGO_URI set
    os.environ.pop("MONGO_URI", None)
    auto_df = get_dataframe(source="auto")
    assert not auto_df.empty
