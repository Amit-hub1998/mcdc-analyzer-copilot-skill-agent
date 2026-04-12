"""
Sample PySpark transformation code for MCDC analysis testing.
This file contains various patterns that the analyzer will detect.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit, coalesce


def process_client_data(df):
    """
    Process client data with various business rules.
    
    MCDC Analyzer will find gaps in this logic!
    """
    
    # Pattern 1: Filter with hardcoded value
    # GAP: Only handles 'ES' - what about 'Y', 'N', NULL?
    active_clients = df.filter(col("client_indicator") == "ES")
    
    # Pattern 2: Complex boolean condition
    # MCDC needs: N+1 = 4 test cases for 3 conditions
    high_value = df.filter(
        (col("status") == "ACTIVE") & 
        (col("amount") > 1000) & 
        (col("risk_flag") == "N")
    )
    
    # Pattern 3: when() chain without complete coverage
    # GAP: What if tier is 'C' or NULL?
    categorized = df.withColumn(
        "category",
        when(col("tier") == "A", "Premium")
        .when(col("tier") == "B", "Standard")
        .otherwise("Unknown")  # At least has otherwise!
    )
    
    # Pattern 4: Multiple when() without otherwise
    # GAP: Missing .otherwise() - what happens for unmatched?
    risk_scored = df.withColumn(
        "risk_score",
        when(col("country") == "US", 1)
        .when(col("country") == "UK", 2)
        .when(col("country") == "DE", 3)
        # Missing: .otherwise(0) or similar!
    )
    
    # Pattern 5: Boundary condition
    # GAP: Is > or >= intended? amount=1000 goes to MEDIUM
    tiered = df.withColumn(
        "size_tier",
        when(col("amount") > 10000, "LARGE")
        .when(col("amount") > 1000, "MEDIUM")
        .when(col("amount") > 0, "SMALL")
        .otherwise("INVALID")
    )
    
    return tiered


def validate_transactions(df):
    """
    Validate transaction data.
    
    Contains if statements for MCDC analysis.
    """
    
    # Pattern 6: Python if with AND
    def check_transaction(row):
        # MCDC needs: 3 test cases for 2 conditions
        if row["amount"] > 0 and row["status"] == "PENDING":
            return "VALID"
        # GAP: What if amount <= 0? What if status is other?
        return "INVALID"
    
    # Pattern 7: Nested conditions
    def categorize_risk(row):
        # Complex logic with multiple gaps
        if row["client_type"] == "RETAIL":
            if row["amount"] > 5000:
                return "HIGH_RISK"
            else:
                return "LOW_RISK"
        elif row["client_type"] == "CORPORATE":
            if row["amount"] > 50000:
                return "HIGH_RISK"
            # GAP: No else for corporate <= 50000!
        # GAP: What if client_type is neither RETAIL nor CORPORATE?
    
    return df


def filter_by_region(df, region_code):
    """
    Filter data by region with multiple conditions.
    """
    
    # Pattern 8: OR condition
    # MCDC: Each condition must independently affect outcome
    if region_code == "EMEA" or region_code == "APAC":
        return df.filter(col("region").isin(["EU", "UK", "ASIA"]))
    elif region_code == "AMER":
        return df.filter(col("region").isin(["US", "CA", "LATAM"]))
    # GAP: What if region_code is something else?
    
    return df


# Main execution
if __name__ == "__main__":
    spark = SparkSession.builder.appName("MCDCDemo").getOrCreate()
    
    # Sample data
    data = [
        ("ES", "ACTIVE", 1500, "N", "A", "US"),
        ("Y", "INACTIVE", 500, "Y", "B", "UK"),
    ]
    columns = ["client_indicator", "status", "amount", "risk_flag", "tier", "country"]
    
    df = spark.createDataFrame(data, columns)
    result = process_client_data(df)
    result.show()
