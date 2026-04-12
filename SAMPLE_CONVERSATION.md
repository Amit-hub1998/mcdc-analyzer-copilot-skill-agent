# 💬 Sample Conversation — MCDC Analyzer in Action

This document shows a real conversation with GitHub Copilot using the MCDC Analyzer skill.

---

## 🎬 Demo Overview

| Step | Action | Result |
|------|--------|--------|
| 1 | Open PySpark file in VS Code | Code loaded |
| 2 | Ask Copilot to analyze | Full MCDC analysis |
| 3 | Request test generation | Pytest file created |

---

## 📝 The Source Code Being Analyzed

**File:** `sample_transformations.py`

```python
def process_client_data(df):
    # Pattern 1: Filter with hardcoded value
    active_clients = df.filter(col("client_indicator") == "ES")
    
    # Pattern 2: Complex boolean condition
    high_value = df.filter(
        (col("status") == "ACTIVE") & 
        (col("amount") > 1000) & 
        (col("risk_flag") == "N")
    )
    
    # Pattern 3: when() chain with otherwise
    categorized = df.withColumn(
        "category",
        when(col("tier") == "A", "Premium")
        .when(col("tier") == "B", "Standard")
        .otherwise("Unknown")
    )
    
    # Pattern 4: when() WITHOUT otherwise (gap!)
    risk_scored = df.withColumn(
        "risk_score",
        when(col("country") == "US", 1)
        .when(col("country") == "UK", 2)
        .when(col("country") == "DE", 3)
        # Missing: .otherwise()
    )
    
    # Pattern 5: Boundary conditions
    tiered = df.withColumn(
        "size_tier",
        when(col("amount") > 10000, "LARGE")
        .when(col("amount") > 1000, "MEDIUM")
        .when(col("amount") > 0, "SMALL")
        .otherwise("INVALID")
    )
    
    return tiered
```

---

## 🗣️ Conversation Part 1: Analysis

### User Prompt
```
Analyze my PySpark code for MCDC coverage
```

### Copilot Response

> *Inspecting the PySpark source file to identify decision points and coverage gaps.*

---

#### MCDC Analysis: sample_transformations.py

---

**Decision 1:** `active_clients = df.filter(col("client_indicator") == "ES")`

| Aspect | Details |
|--------|---------|
| **Atomic condition** | `client_indicator == "ES"` |
| **MCDC test cases** | • `"ES"` → included<br>• `!= "ES"` / `NULL` → excluded |
| **⚠️ Logic gap** | Only handles `"ES"`<br>Missing: `"Y"`, `"N"`, `NULL`, empty string |

---

**Decision 2:** `high_value = df.filter((col("status") == "ACTIVE") & (col("amount") > 1000) & (col("risk_flag") == "N"))`

| Aspect | Details |
|--------|---------|
| **Atomic conditions** | 1. `status == "ACTIVE"`<br>2. `amount > 1000`<br>3. `risk_flag == "N"` |
| **MCDC test cases (N+1 = 4)** | • All true<br>• First false, others true<br>• Second false, others true<br>• Third false, others true |
| **⚠️ Logic gaps** | • No handling for `status = "INACTIVE"`<br>• No `amount = 1000` boundary check<br>• No `risk_flag` values other than `"N"` or `NULL` |

---

**Decision 3:** `when(col("tier") == "A", "Premium").when(col("tier") == "B", "Standard").otherwise("Unknown")`

| Aspect | Details |
|--------|---------|
| **Atomic conditions** | 1. `tier == "A"`<br>2. `tier == "B"` |
| **MCDC test cases** | • `"A"` → Premium<br>• `"B"` → Standard<br>• `"C"` / `NULL` → Unknown |
| **✅ Notes** | Has `.otherwise()` — default is covered<br>Still should test `NULL` and unexpected values |

---

**Decision 4:** `risk_score` with three `when()` calls and **no `.otherwise()`**

| Aspect | Details |
|--------|---------|
| **Atomic conditions** | 1. `country == "US"`<br>2. `country == "UK"`<br>3. `country == "DE"` |
| **MCDC test cases** | • `US` → 1<br>• `UK` → 2<br>• `DE` → 3<br>• other / `NULL` → ❓ missing output |
| **🔴 Critical gap** | No `.otherwise(...)` — unmatched countries produce `NULL` risk score |

---

**Decision 5:** `size_tier` with boundary conditions

| Aspect | Details |
|--------|---------|
| **Atomic conditions** | 1. `amount > 10000`<br>2. `amount > 1000`<br>3. `amount > 0` |
| **MCDC/boundary cases** | • `15000` → LARGE<br>• `5000` → MEDIUM<br>• `500` → SMALL<br>• `0` or negative → INVALID |
| **⚠️ Logic gaps** | • Boundary ambiguity at `10000`, `1000`, `0`<br>• No explicit `NULL` handling |

---

**Decision 6:** `if row["amount"] > 0 and row["status"] == "PENDING":`

| Aspect | Details |
|--------|---------|
| **Atomic conditions** | 1. `amount > 0`<br>2. `status == "PENDING"` |
| **MCDC test cases (N+1 = 3)** | • Valid amount + pending status<br>• Invalid amount + pending status<br>• Valid amount + non-pending status |
| **⚠️ Gap** | • No test for `status = NULL`<br>• No coverage for `amount = 0` or negative |

---

**Decision 7:** Nested risk categorization in `categorize_risk()`

| Aspect | Details |
|--------|---------|
| **Key branches** | 1. `client_type == "RETAIL"`<br>2. nested `amount > 5000`<br>3. `client_type == "CORPORATE"`<br>4. nested `amount > 50000` |
| **Required tests** | • RETAIL, amount > 5000<br>• RETAIL, amount <= 5000<br>• CORPORATE, amount > 50000<br>• CORPORATE, amount <= 50000<br>• Other client_type |
| **🔴 Major gaps** | • Corporate branch has no `else` for amount <= 50000<br>• Client types outside RETAIL/CORPORATE return `None`<br>• No NULL handling |

---

**Decision 8:** `filter_by_region(df, region_code)`

| Aspect | Details |
|--------|---------|
| **Conditions** | 1. `region_code == "EMEA"`<br>2. `region_code == "APAC"`<br>3. `region_code == "AMER"` |
| **MCDC test cases** | • EMEA → EMEA filter<br>• APAC → APAC filter<br>• AMER → AMER filter<br>• LATAM / other → returns original `df` |
| **⚠️ Gap** | • No explicit handling for invalid `region_code`<br>• `region_code = NULL` not covered |

---

### 📊 Summary of Coverage Risks

| Risk Type | Examples |
|-----------|----------|
| **Hardcoded values** | `client_indicator == "ES"`, `risk_flag == "N"`, `tier`, `country` |
| **Missing otherwise/default** | `risk_score`, corporate low-risk branch, unknown client types |
| **Boundary and NULL cases** | `amount > 1000`, `amount > 10000`, `amount > 0`, `status == "PENDING"` |
| **OR-condition MCDC** | `region_code == "EMEA" or region_code == "APAC"` needs independent tests |

---

## 🗣️ Conversation Part 2: Test Generation

### User Prompt
```
Generate pytest test cases based on the MCDC analysis above
```

### Copilot Response

> *Pytest Coverage Added*
> 
> Created `test_sample_transformations.py` with MCDC-focused scenarios:

**Generated Tests:**
- `test_process_client_data_category_and_risk_score_and_size_tier`
- `test_process_client_data_risk_score_unmatched_country_is_null`
- `test_process_client_data_size_tier_boundaries`
- `test_filter_by_region_emea_and_apac_share_the_same_valid_regions`
- `test_validate_transactions_returns_original_dataframe`

**Notes:**
- Covers visible logic in `process_client_data()` and `filter_by_region()`
- Includes boundary checks for `amount` and null/unmatched `country`
- `validate_transactions()` is currently a passthrough, so test verifies return identity

---

## 📸 Screenshots

> **Note:** Add your own screenshots here showing the VS Code interface.

### Screenshot 1: Analysis Request
```
[Insert screenshot of Copilot Chat with the analysis prompt]
```

### Screenshot 2: Analysis Output
```
[Insert screenshot showing the MCDC analysis results]
```

### Screenshot 3: Test Generation
```
[Insert screenshot showing the generated test file]
```

---

## 🎯 Key Takeaways

1. **8 decision points** identified automatically
2. **Multiple logic gaps** found without running any code
3. **N+1 test cases** generated for each complex condition
4. **Critical gap found**: `risk_score` missing `.otherwise()`
5. **Pytest tests generated** with one follow-up prompt

---

## 🔁 Try It Yourself

1. Copy the `.github/skills/mcdc-analyzer/` folder to your repo
2. Open any PySpark file in VS Code
3. Open Copilot Chat (Ctrl+Shift+I / Cmd+Shift+I)
4. Type: `Analyze this code for MCDC coverage`
5. Follow up with: `Generate pytest tests`

---

<p align="center">
  <b>The skill works on any Python/PySpark code with conditions!</b>
</p>
