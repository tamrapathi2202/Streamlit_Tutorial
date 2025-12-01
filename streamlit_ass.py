import os
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from typing import Optional

from streamlit_utils import (
    get_dataframe as utils_get_dataframe,
    get_mongo_client as utils_get_mongo_client,
    try_import_pymongo as utils_try_import_pymongo,
    load_csv_data as utils_load_csv_data,
)


st.set_page_config(page_title="Sales Dashboard (Assignment)", layout="wide")

st.title("📊 Sales Performance — extra assignment dashboard")

with st.form("login_form", clear_on_submit=False):
    username = st.text_input("Enter a display name (optional)")
    submitted = st.form_submit_button("Continue")

if submitted and username:
    st.success(f"Hi, {username}! Welcome — filters are on the left.")
else:
    st.info("Enter a name (optional) to personalise the dashboard.")


try_import_pymongo = utils_try_import_pymongo
get_mongo_client = utils_get_mongo_client
load_csv_data = utils_load_csv_data
get_dataframe = utils_get_dataframe


# pick data source
DATA_SOURCE = os.environ.get("DATA_SOURCE", "auto").lower()
MONGO_URI = os.environ.get("MONGO_URI")
MONGO_DB = os.environ.get("MONGO_DB")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION")

df = get_dataframe(
    source=DATA_SOURCE,
    mongo_uri=MONGO_URI,
    mongo_db=MONGO_DB,
    mongo_collection=MONGO_COLLECTION,
)

# --- Sidebar controls (mirroring your friend's structure) ---
st.sidebar.header("Filters & Controls")

st.sidebar.markdown(
    "Choose a data source (auto = MongoDB if MONGO_URI is set, otherwise CSV)"
)
source_choice = st.sidebar.selectbox("Data source", ["auto", "csv", "mongo"], index=0)

if source_choice != DATA_SOURCE:
    # If user explicitly chooses and we can load, reload (informational only — caches will make it cheap)
    if source_choice == "csv":
        df = get_dataframe(source="csv")
    elif source_choice == "mongo":
        if not MONGO_URI:
            st.sidebar.warning(
                "MONGO_URI not set — continue by setting env var MONGO_URI."
            )
        else:
            df = get_dataframe(
                source="mongo",
                mongo_uri=MONGO_URI,
                mongo_db=MONGO_DB,
                mongo_collection=MONGO_COLLECTION,
            )

view_format = st.sidebar.radio("Select View Format", ["Table View", "JSON View"])

regions = (
    st.sidebar.multiselect(
        "Region",
        options=sorted(df["region"].unique()),
        default=sorted(df["region"].unique()),
    )
    if "region" in df.columns
    else []
)
categories = (
    st.sidebar.multiselect(
        "Category",
        options=sorted(df["category"].unique()),
        default=sorted(df["category"].unique()),
    )
    if "category" in df.columns
    else []
)
segments = (
    st.sidebar.multiselect(
        "Customer segment",
        options=sorted(df["customer_segment"].unique()),
        default=sorted(df["customer_segment"].unique()),
    )
    if "customer_segment" in df.columns
    else []
)

min_date = df["order_date"].min().date() if "order_date" in df.columns else None
max_date = df["order_date"].max().date() if "order_date" in df.columns else None
date_range = (
    st.sidebar.date_input(
        "Order date range",
        value=(min_date, max_date) if min_date and max_date else None,
        min_value=min_date,
        max_value=max_date,
    )
    if min_date and max_date
    else None
)

st.sidebar.markdown("---")
download_all = st.sidebar.button("Download full dataset")

# Apply filters
filtered = df.copy()
if regions and "region" in filtered.columns:
    filtered = filtered[filtered["region"].isin(regions)]
if categories and "category" in filtered.columns:
    filtered = filtered[filtered["category"].isin(categories)]
if segments and "customer_segment" in filtered.columns:
    filtered = filtered[filtered["customer_segment"].isin(segments)]
if (
    date_range
    and isinstance(date_range, tuple)
    and len(date_range) == 2
    and "order_date" in filtered.columns
):
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = filtered[filtered["order_date"].between(start, end)]

if filtered.empty:
    st.warning("No records match your filters — adjust controls in the sidebar.")

# --- KPIs ---
st.subheader("Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)
total_sales = (
    float(filtered["sales"].sum())
    if not filtered.empty and "sales" in filtered.columns
    else 0.0
)
total_profit = (
    float(filtered["profit"].sum())
    if not filtered.empty and "profit" in filtered.columns
    else 0.0
)
avg_margin = (total_profit / total_sales * 100) if total_sales else 0.0
avg_order = (
    filtered["sales"].mean()
    if not filtered.empty and "sales" in filtered.columns
    else 0.0
)

col1.metric("Total sales", f"${total_sales:,.0f}")
col2.metric("Total profit", f"${total_profit:,.0f}")
col3.metric("Avg margin", f"{avg_margin:.1f}%")
col4.metric("Avg order", f"${avg_order:,.0f}")

st.divider()

# --- Raw Data View ---
st.subheader("📂 Raw Data View")
if view_format == "Table View":
    st.dataframe(filtered.head(50), use_container_width=True)
else:
    st.json(filtered.head(50).to_dict(orient="records"))

    # Data editor for on-the-fly edits (in-memory only)
    if not filtered.empty:
        st.subheader("📝 Edit filtered rows (in-memory)")
        original_subset = filtered.reset_index(drop=True).head(20)
        edited = st.data_editor(
            original_subset,
            num_rows="dynamic",
            use_container_width=True,
        )

        if not edited.equals(original_subset):
            st.info(
                "Local edits detected — you can keep them in-memory or persist to the DB (when available)."
            )

            # Persist back to MongoDB if possible
            mongo_client = (
                get_mongo_client(MONGO_URI)
                if MONGO_URI and try_import_pymongo()
                else None
            )

            if mongo_client and source_choice in ("auto", "mongo"):
                st.warning(
                    "A MongoDB connection is available. You can persist these edited rows back to the collection."
                )
                persist = st.checkbox("Enable write-back to MongoDB for these edits")

                if persist:
                    confirm = st.button("Save edits to MongoDB")
                    if confirm:
                        # run update for each changed row
                        from bson import ObjectId  # type: ignore

                        db_name = MONGO_DB or os.environ.get("MONGO_DB", "sales_db")
                        coll_name = MONGO_COLLECTION or os.environ.get(
                            "MONGO_COLLECTION", "sales"
                        )
                        coll = mongo_client[db_name][coll_name]

                        updates = 0
                        for idx, row in edited.iterrows():
                            orig = original_subset.iloc[idx].to_dict()
                            new = row.to_dict()

                            # identify _id field
                            if "_id" not in new or not new.get("_id"):
                                st.error(
                                    "No _id available for row — cannot persist row to MongoDB (missing _id)."
                                )
                                continue

                            _id_str = str(new["_id"])
                            try:
                                oid = ObjectId(_id_str)
                            except Exception:
                                st.error(
                                    f"_id {_id_str} is not a valid ObjectId; skipping row."
                                )
                                continue

                            # compute changed fields and prepare update payload
                            changed = {}
                            for k, v in new.items():
                                if k == "_id":
                                    continue
                                orig_v = orig.get(k)
                                # pandas timestamps -> python datetime for Mongo
                                if hasattr(v, "to_pydatetime"):
                                    v_to_store = v.to_pydatetime()
                                else:
                                    v_to_store = v

                                if pd.isna(v_to_store) and pd.isna(orig_v):
                                    continue
                                if v_to_store != orig_v:
                                    changed[k] = v_to_store

                            if changed:
                                result = coll.update_one(
                                    {"_id": oid}, {"$set": changed}
                                )
                                if result.modified_count > 0:
                                    updates += 1

                        st.success(
                            f"Persisted {updates} row(s) to {db_name}.{coll_name}"
                        )
            else:
                st.info(
                    "No MongoDB client available (or not selected). Edits remain in-memory only."
                )

st.divider()

# --- Advanced visualizations in tabs ---
st.subheader("📊 Visual Analysis")
tab1, tab2, tab3 = st.tabs(
    ["Sales Trend", "Category / Subcategory", "Profit by Segment"]
)

with tab1:
    st.markdown("### Sales over time")
    if not filtered.empty and "order_date" in filtered.columns:
        sales_trend = filtered.groupby("order_date", as_index=False)["sales"].sum()
        fig = px.line(
            sales_trend,
            x="order_date",
            y="sales",
            title="Daily sales trend",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data to chart.")

with tab2:
    st.markdown("### Sales by Category & Subcategory")
    if not filtered.empty and "category" in filtered.columns:
        cat = (
            filtered.groupby(["category", "subcategory"], as_index=False)["sales"].sum()
            if "subcategory" in filtered.columns
            else filtered.groupby(["category"], as_index=False)["sales"].sum()
        )
        fig = px.bar(
            cat,
            x=cat.columns[0],
            y="sales",
            color="category" if "subcategory" in cat.columns else None,
            title="Sales by subcategory",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data to chart.")

with tab3:
    st.markdown("### Profit contribution by customer segment")
    if (
        not filtered.empty
        and "customer_segment" in filtered.columns
        and "profit" in filtered.columns
    ):
        seg = filtered.groupby("customer_segment", as_index=False)["profit"].sum()
        fig = px.pie(
            seg,
            names="customer_segment",
            values="profit",
            title="Profit contribution",
            hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data to chart.")

st.divider()

# --- Download buttons ---
st.subheader("📥 Download")
if download_all:
    st.download_button(
        "Download full dataset",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="sales_sample.csv",
        mime="text/csv",
    )

st.download_button(
    "Download filtered data",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_sales.csv",
    mime="text/csv",
)

st.caption(
    "This file follows the structure of the example you shared but supports an optional MongoDB backend via MONGO_URI and keeps a CSV fallback so it works out-of-the-box."
)
