---
name: mcdc-analyzer
description: Analyze PySpark/Python code for MCDC (Modified Condition/Decision Coverage) test gaps. Use this when asked to find missing test cases, analyze code coverage, identify logic gaps, generate test scenarios, or check if all branches are covered. Triggers on phrases like "analyze for MCDC", "find missing tests", "check coverage", "logic gaps", "negative test cases", "branch coverage", "what if scenarios".
license: MIT
allowed-tools:
  - python
  - shell
---

# MCDC Code Analyzer Skill

You are an expert in **Modified Condition/Decision Coverage (MCDC)** testing and static code analysis. Your job is to analyze PySpark and Python data transformation code WITHOUT executing it, identifying:

1. **Logic Gaps**: Missing branches (e.g., code handles `client_indicator == 'ES'` but not other values)
2. **MCDC Test Cases**: Generate N+1 test cases where N = number of atomic conditions
3. **Negative Scenarios**: Edge cases, null handling, format issues
4. **Uncovered Branches**: Conditions that aren't fully tested

## What is MCDC?

MCDC (Modified Condition/Decision Coverage) requires that:
- Every entry and exit point is invoked
- Every condition takes all possible outcomes (True/False)
- Each condition independently affects the decision outcome

For a condition like `A and B and C`, MCDC requires N+1 = 4 test cases (not 2^3 = 8).

## How to Analyze Code

### Step 1: Extract All Conditions

Look for these patterns in the code:

**Python if statements:**
```python
if client_indicator == 'ES' and amount > 1000:
    # condition with 2 atomic conditions
```

**PySpark filter/where:**
```python
df.filter(col("status") == "ACTIVE")
df.where((col("amount") > 0) & (col("flag") == "Y"))
```

**PySpark when/otherwise:**
```python
when(col("type") == "A", "Category1")
.when(col("type") == "B", "Category2")
.otherwise("Unknown")
```

### Step 2: Identify Atomic Conditions

Break down each decision into atomic conditions:

| Decision | Atomic Conditions |
|----------|-------------------|
| `A and B` | A, B |
| `(X > 10) or (Y == 'Z')` | X > 10, Y == 'Z' |
| `not (A and B)` | A, B |

### Step 3: Generate MCDC Test Cases

For each decision with N conditions, generate N+1 test cases where each condition independently affects the outcome.

**Example for `A and B`:**
| Test | A | B | Result | Tests |
|------|---|---|--------|-------|
| 1 | T | T | T | Base case |
| 2 | F | T | F | A independence |
| 3 | T | F | F | B independence |

### Step 4: Find Logic Gaps

Check for these common gaps:

1. **Missing else/otherwise**: What happens when no condition matches?
2. **Hardcoded values**: `== 'ES'` - what about 'Y', 'N', other codes?
3. **No null handling**: What if the column is NULL?
4. **Boundary conditions**: `> 1000` - what about exactly 1000?
5. **Type mismatches**: String vs Integer comparisons
6. **Empty strings**: What if value is '' (empty)?

### Step 5: Generate Negative Test Scenarios

For each variable in conditions, consider:
- NULL / None
- Empty string ''
- Unexpected type (string where number expected)
- Boundary values (0, -1, MAX_INT)
- Special characters
- Whitespace

## Output Format

When analyzing code, provide output in this structure:

```
## MCDC Analysis Report

### Condition 1: [Line X]
**Code:** `if client_indicator == 'ES' and amount > 1000:`

**Atomic Conditions:**
1. client_indicator == 'ES'
2. amount > 1000

**MCDC Test Cases (N+1 = 3):**
| # | client_indicator | amount | Expected | Purpose |
|---|------------------|--------|----------|---------|
| 1 | 'ES' | 1500 | True | Base case - all true |
| 2 | 'Y' | 1500 | False | Tests condition 1 independence |
| 3 | 'ES' | 500 | False | Tests condition 2 independence |

**Logic Gaps Detected:**
⚠️ Only 'ES' handled - what about: 'Y', 'N', NULL, empty?
⚠️ No explicit NULL check for client_indicator
⚠️ Boundary: amount = 1000 not covered (> vs >=)

**Negative Test Scenarios:**
| Scenario | client_indicator | amount | Expected Behavior |
|----------|------------------|--------|-------------------|
| Null indicator | NULL | 1500 | ❓ Undefined |
| Empty string | '' | 1500 | ❓ Undefined |
| Null amount | 'ES' | NULL | ❓ Undefined |
| Negative amount | 'ES' | -100 | ❓ Should this pass? |
| Boundary exact | 'ES' | 1000 | False (> not >=) |
```

## Using the Analysis Script

For automated analysis, run the [analyze.py](./analyze.py) script:

```bash
python analyze.py path/to/your/code.py
```

Or for Jupyter notebooks:
```bash
python analyze.py path/to/notebook.ipynb
```

The script will:
1. Parse the code using Python's AST module (no execution)
2. Extract all conditions from if/filter/when statements
3. Generate MCDC test cases
4. Identify logic gaps
5. Output a structured report

## Common PySpark Patterns to Watch

### Pattern 1: Chained when() without otherwise()
```python
# GAP: What if type is 'C'?
df.withColumn("cat", 
    when(col("type") == "A", "Cat1")
    .when(col("type") == "B", "Cat2"))  # Missing .otherwise()
```

### Pattern 2: Filter without null handling
```python
# GAP: Rows with NULL status are silently dropped
df.filter(col("status") == "ACTIVE")
```

### Pattern 3: Complex boolean logic
```python
# MCDC needed: 4 test cases for 3 conditions
df.filter(
    (col("a") == 1) & 
    ((col("b") > 10) | (col("c").isNotNull()))
)
```

## Integration with Your Workflow

After generating test cases:
1. Create actual pytest/unittest tests from the scenarios
2. Add the tests to your test suite
3. Run against sample data to verify logic
4. Document any intentional gaps

## Questions to Ask About Your Code

When analyzing, always consider:
- "What happens if this value is NULL?"
- "What if this string is empty?"
- "Are there other valid values besides the ones handled?"
- "What's the boundary behavior?"
- "Is this filter inclusive or exclusive?"
