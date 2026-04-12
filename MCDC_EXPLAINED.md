# 📚 MCDC (Modified Condition/Decision Coverage) Explained

## What is MCDC?

**MCDC** is a code coverage criterion that ensures:

1. Every **entry and exit point** is invoked
2. Every **condition** takes all possible outcomes (True/False)  
3. Each condition **independently affects** the decision outcome

## Why MCDC?

### The Problem with Exhaustive Testing

For a condition like `A and B and C`:

| Coverage Type | Test Cases Required | Practical? |
|---------------|---------------------|------------|
| Statement Coverage | 1 | ✅ Too weak |
| Decision Coverage | 2 | ✅ Still weak |
| Multiple Condition (MCC) | 2³ = **8** | ❌ Explodes! |
| **MCDC** | N+1 = **4** | ✅ Balanced |

### For Real-World Code

| Conditions in Decision | MCC Tests | MCDC Tests | Savings |
|------------------------|-----------|------------|---------|
| 3 | 8 | 4 | 50% |
| 5 | 32 | 6 | 81% |
| 10 | 1,024 | 11 | 99% |
| 20 | 1,048,576 | 21 | 99.998% |

## The N+1 Formula

For **N atomic conditions**, MCDC requires only **N+1 test cases**.

### Example: `A and B and C`

We need to show each condition **independently** affects the outcome:

| Test | A | B | C | Result | What It Proves |
|------|---|---|---|--------|----------------|
| 1 | T | T | T | **True** | Base case |
| 2 | **F** | T | T | **False** | A independently affects result |
| 3 | T | **F** | T | **False** | B independently affects result |
| 4 | T | T | **F** | **False** | C independently affects result |

**Key insight:** In each test (2, 3, 4), only ONE condition changes from the base case, and the result changes. This proves **independence**.

## AND vs OR Logic

### For `A and B` (AND logic)

| Test | A | B | Result | Purpose |
|------|---|---|--------|---------|
| 1 | T | T | T | Base (both true) |
| 2 | F | T | F | A independence |
| 3 | T | F | F | B independence |

### For `A or B` (OR logic)

| Test | A | B | Result | Purpose |
|------|---|---|--------|---------|
| 1 | F | F | F | Base (both false) |
| 2 | T | F | T | A independence |
| 3 | F | T | T | B independence |

## Mixed Logic

For `A and (B or C)`:

First, identify the structure:
- Outer: AND (A, inner)
- Inner: OR (B, C)

Test cases:
1. A=T, B=T, C=T → T (base for AND with inner=T)
2. A=F, B=T, C=T → F (A independence)
3. A=T, B=F, C=F → F (inner independence)
4. A=T, B=T, C=F → T (B independence within OR)
5. A=T, B=F, C=T → T (C independence within OR)

## Real-World Example: PySpark

```python
df.filter(
    (col("status") == "ACTIVE") & 
    (col("amount") > 1000) & 
    (col("risk_flag") == "N")
)
```

**Atomic conditions (N=3):**
1. `status == "ACTIVE"`
2. `amount > 1000`
3. `risk_flag == "N"`

**MCDC Test Cases (N+1=4):**

| Test | status | amount | risk_flag | Passes Filter | Purpose |
|------|--------|--------|-----------|---------------|---------|
| 1 | ACTIVE | 1500 | N | ✅ Yes | Base case |
| 2 | INACTIVE | 1500 | N | ❌ No | status independence |
| 3 | ACTIVE | 500 | N | ❌ No | amount independence |
| 4 | ACTIVE | 1500 | Y | ❌ No | risk_flag independence |

## Where MCDC is Required

| Industry | Standard | Requirement |
|----------|----------|-------------|
| Aviation | DO-178C | 100% MCDC for DAL-A software |
| Automotive | ISO 26262 | MCDC for ASIL-D |
| Medical | IEC 62304 | MCDC for Class C |
| Space | NASA NPR 7150.2D | 100% MCDC for safety-critical |
| General | IEC 61508 | MCDC for SIL-4 |

## Common Mistakes

### ❌ Mistake 1: Testing all combinations
```
Don't test 2^N combinations — that's MCC, not MCDC!
```

### ❌ Mistake 2: Changing multiple conditions at once
```
Each test should flip exactly ONE condition from a reference test.
```

### ❌ Mistake 3: Ignoring short-circuit evaluation
```python
if A and B:  # If A is False, B is never evaluated
```

### ❌ Mistake 4: Forgetting boundary conditions
```python
if amount > 1000:  # What about amount = 1000?
```

## Quick Reference

| Formula | Meaning |
|---------|---------|
| **N** | Number of atomic conditions |
| **N+1** | Minimum MCDC test cases |
| **2^N** | MCC test cases (avoid!) |

| Operator | Base Case | Independence Test |
|----------|-----------|-------------------|
| AND | All True | Flip one to False → Result changes |
| OR | All False | Flip one to True → Result changes |
| NOT | Opposite | Flip → Result changes |

---

## References

- [NASA MCDC Tutorial (PDF)](https://ntrs.nasa.gov/api/citations/20040086014/downloads/20040086014.pdf)
- [DO-178C Standard](https://en.wikipedia.org/wiki/DO-178C)
- [ISO 26262 Automotive Safety](https://en.wikipedia.org/wiki/ISO_26262)
- [LDRA MCDC Guide](https://ldra.com/capabilities/mc-dc/)
