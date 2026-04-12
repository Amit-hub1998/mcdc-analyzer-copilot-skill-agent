import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

import sample_transformations as st


@pytest.fixture(scope="session")
def spark():
    spark_session = SparkSession.builder.master("local[2]").appName("pytest_sample_transformations").getOrCreate()
    yield spark_session
    spark_session.stop()


def test_process_client_data_category_and_risk_score_and_size_tier(spark):
    data = [
        ("ES", "ACTIVE", 1500, "N", "A", "US"),
        ("Y", "ACTIVE", 500, "Y", "C", "FR"),
        ("N", "INACTIVE", 15000, "N", "B", "UK"),
        (None, "ACTIVE", 2000, "N", None, "AU"),
    ]
    columns = [
        "client_indicator",
        "status",
        "amount",
        "risk_flag",
        "tier",
        "country",
    ]
    df = spark.createDataFrame(data, columns)

    result = st.process_client_data(df)
    rows = result.select("category", "risk_score", "size_tier").collect()

    assert rows[0][0] == "Premium"
    assert rows[0][1] == 1
    assert rows[0][2] == "MEDIUM"

    assert rows[1][0] == "Unknown"
    assert rows[1][1] is None
    assert rows[1][2] == "SMALL"

    assert rows[2][0] == "Standard"
    assert rows[2][1] == 2
    assert rows[2][2] == "LARGE"

    assert rows[3][0] == "Unknown"
    assert rows[3][1] is None
    assert rows[3][2] == "MEDIUM"


def test_process_client_data_risk_score_unmatched_country_is_null(spark):
    data = [
        ("ES", "ACTIVE", 1200, "N", "A", "FR"),
        ("ES", "ACTIVE", 1200, "N", "A", None),
    ]
    columns = ["client_indicator", "status", "amount", "risk_flag", "tier", "country"]
    df = spark.createDataFrame(data, columns)

    result = st.process_client_data(df)
    risk_scores = [row[0] for row in result.select("risk_score").collect()]
    assert risk_scores == [None, None]


def test_process_client_data_size_tier_boundaries(spark):
    data = [
        (10001,),
        (10000,),
        (1000,),
        (1,),
        (0,),
        (-1,),
        (None,),
    ]
    columns = ["amount"]
    df = spark.createDataFrame(data, columns)

    result = st.process_client_data(df)
    size_tiers = [row[0] for row in result.select("size_tier").collect()]

    assert size_tiers == ["LARGE", "MEDIUM", "SMALL", "SMALL", "INVALID", "INVALID", "INVALID"]


def test_filter_by_region_emea_and_apac_share_the_same_valid_regions(spark):
    data = [
        ("EU",),
        ("UK",),
        ("ASIA",),
        ("US",),
        ("CA",),
        ("LATAM",),
    ]
    columns = ["region"]
    df = spark.createDataFrame(data, columns)

    emea_df = st.filter_by_region(df, "EMEA")
    apac_df = st.filter_by_region(df, "APAC")
    amer_df = st.filter_by_region(df, "AMER")
    other_df = st.filter_by_region(df, "OTHER")

    assert sorted([row[0] for row in emea_df.collect()]) == ["ASIA", "EU", "UK"]
    assert sorted([row[0] for row in apac_df.collect()]) == ["ASIA", "EU", "UK"]
    assert sorted([row[0] for row in amer_df.collect()]) == ["CA", "LATAM", "US"]
    assert sorted([row[0] for row in other_df.collect()]) == ["ASIA", "CA", "EU", "LATAM", "UK", "US"]


def test_validate_transactions_returns_original_dataframe(spark):
    data = [(1, "PENDING"), (2, "COMPLETE")]
    columns = ["amount", "status"]
    df = spark.createDataFrame(data, columns)

    result = st.validate_transactions(df)
    assert result.count() == df.count()
    assert result.columns == df.columns
    assert sorted(result.collect()) == sorted(df.collect())
