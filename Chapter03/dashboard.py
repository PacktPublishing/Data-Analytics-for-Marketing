import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Marketing Dashboard", layout="wide")

data_df = pd.read_csv("data/campaign_data.csv", parse_dates=[0])
data_df["year"] = data_df["utc_date"].dt.year
data_df["campaign_name"] = data_df["campaign_url"].str.replace(
    "https://www.example.com/", "", regex=False
)


with st.sidebar:
    min_date = min(data_df.utc_date)
    max_date = max(data_df.utc_date)
    start_date = st.date_input("Pick Start date", min_date)
    end_date = st.date_input("Pick End date", max_date)

    platforms = data_df.traffic_source.unique()
    platforms = np.append(platforms, "All")
    default_platform = len(platforms) - 1
    CM_Platform = st.selectbox(
        "Select Media Platform", platforms, index=default_platform
    )

    countries = data_df.country.unique()
    countries = np.append(countries, "All")
    default_country = len(countries) - 1
    CM_Country = st.selectbox("Select Country", countries, index=default_country)

    devices = data_df.device_viewed.unique()
    devices = np.append(devices, "All")
    default_device = len(devices) - 1
    CM_Device = st.selectbox("Select Device", devices, index=default_device)

    accounts = data_df.account_name.unique()
    accounts = np.append(accounts, "All")
    default_account = len(accounts) - 1
    CM_Account = st.selectbox("Select Account", accounts, index=default_account)

    campaigns = data_df.campaign_name.unique()
    campaigns = np.append(campaigns, "All")
    default_campaign = len(campaigns) - 1
    CM_Campaign = st.selectbox("Select Campaign", accounts, index=default_campaign)


def get_metrics(data: pd.DataFrame, st_object):
    impressions = data.loc[:, "impressions"].sum()
    clicks = data.loc[:, "page_clicks"].sum()
    ctr = round(
        100.0 * data.loc[:, "page_clicks"].sum() / data.loc[:, "impressions"].sum(), 2
    )
    gross_profit = round(data.loc[:, "gross_profit"].sum(), 2)
    avg_cpc = round(data.loc[:, "cpc"].mean(), 2)
    avg_rpc = round(data.loc[:, "rpc"].mean(), 2)

    col1, col2, col3, col4, col5, col6 = st_object.columns(6)

    col1.metric("Total Impressions", impressions)
    col2.metric("Total Clicks", clicks)
    col3.metric("CTR", f"{ctr}%")
    col4.metric("Total Gross Profit", f"{gross_profit/1000:.2f}k $")
    col5.metric("Avg Cost Per Click", f"{avg_cpc:.2f} $")
    col6.metric("Avg Rev Per Click", f"{avg_rpc:.2f} $")


def top_traffic_source(data: pd.DataFrame) -> pd.DataFrame:
    top_traffic_sources = (
        data.groupby(by=["traffic_source"])
        .agg(
            {
                "impressions": "sum",
                "page_clicks": "sum",
                "revenue": "sum",
                "ad_spend": "sum",
                "gross_profit": "sum",
                "cpc": "mean",
                "rpc": "mean",
                "cpa": "mean",
            }
        )
        .reset_index()
    )

    return top_traffic_sources


def top_campaign(data: pd.DataFrame) -> pd.DataFrame:
    top_campaigns = (
        data.groupby(by=["account_name", "campaign_name"])
        .agg(
            {
                "impressions": "sum",
                "page_clicks": "sum",
                "revenue": "sum",
                "ad_spend": "sum",
                "gross_profit": "sum",
                "cpc": "mean",
                "rpc": "mean",
                "cpa": "mean",
                "roas": "mean",
            }
        )
        .reset_index()
    )

    return top_campaigns


def generate_column_charts(data: pd.DataFrame, column: str = "impressions"):
    monthly_data = (
        data.groupby(pd.Grouper(key="utc_date", freq="M"))
        .agg({column: "sum"})
        .reset_index()
    )

    fig = px.bar(
        monthly_data,
        x="utc_date",
        y=column,
        labels={"value": "Count"},
        title=f"Monthly {column}",
    )

    return fig


def generated_stacked_campaign_charts(data: pd.DataFrame, column: str = "impressions"):
    monthly_data = (
        data.groupby([pd.Grouper(key="utc_date", freq="M"), "campaign_name"])
        .agg({column: "sum"})
        .reset_index()
    )

    fig = px.bar(
        monthly_data,
        x="utc_date",
        y=column,
        color="campaign_name",
        title=f"{column} by Campaign",
        labels={column: column, "campaign_name": "Campaign"},
    )

    fig.update_layout(barmode="stack")

    return fig


filter_conditions = []
# Update filter_conditions based on user selections
if CM_Platform != "All":
    filter_conditions.append(f"traffic_source == '{CM_Platform}'")

if CM_Country != "All":
    filter_conditions.append(f"country == '{CM_Country}'")

if CM_Device != "All":
    filter_conditions.append(f"device_viewed == '{CM_Device}'")

if CM_Account != "All":
    filter_conditions.append(f"account_name == '{CM_Account}'")

if CM_Campaign != "All":
    filter_conditions.append(f"campaign_name == '{CM_Campaign}'")
# Combine all filter conditions into a single string using 'and'
filter_condition = " and ".join(filter_conditions)

# Apply the dynamically constructed filter to the dataframe
if filter_condition:  # Check if there is any condition to apply
    data_filtered = data_df.query(filter_condition)
else:
    data_filtered = data_df  # No filter applied, use the original DataFrame

if start_date and end_date:
    data_filtered = data_filtered[
        (data_filtered["utc_date"] >= pd.to_datetime(start_date))
        & (data_filtered["utc_date"] <= pd.to_datetime(end_date))
    ]

get_metrics(data_filtered, st)


row1_col1, row1_col2 = st.columns(2)
row1_col1.plotly_chart(generate_column_charts(data_filtered, "impressions"))
row1_col2.plotly_chart(generate_column_charts(data_filtered, "gross_profit"))


st.subheader("Sources Metrics")
st.dataframe(top_traffic_source(data_filtered), use_container_width=True)

st.subheader("Campaign Stats")
row2_col1, row2_col2 = st.columns(2)
row2_col1.plotly_chart(generated_stacked_campaign_charts(data_filtered, "impressions"))
row2_col2.plotly_chart(generated_stacked_campaign_charts(data_filtered, "gross_profit"))
st.dataframe(top_campaign(data_filtered), use_container_width=True)
