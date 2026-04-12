# 🧪 MCDC Analyzer — GitHub Copilot Skill

> **Static code analysis for Modified Condition/Decision Coverage (MCDC) in PySpark/Python**  
> Works directly in VS Code with GitHub Copilot — no external tools required.


[![Copilot Skill](https://img.shields.io/badge/GitHub-Copilot%20Skill-8957e5)](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)

---

## 🎯 What It Does

This skill teaches GitHub Copilot to analyze your data transformation code and find **testing gaps** — without executing any code.

| Feature | Description |
|---------|-------------|
| **Logic Gap Detection** | Finds missing branches (e.g., handles `'ES'` but not `'Y'`, `NULL`) |
| **MCDC Test Cases** | Generates **N+1** test cases for **N** atomic conditions |
| **Negative Scenarios** | Identifies NULL handling, boundary conditions, edge cases |
| **Pytest Generation** | Automatically generates test files from analysis |

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  VS Code + GitHub Copilot                                           │
│  ┌──────────┐    ┌─────────────┐    ┌─────────────────────────────┐│
│  │ Your Code│ →  │ Copilot Chat│ →  │ "Analyze for MCDC coverage" ││
│  └──────────┘    └─────────────┘    └─────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                              │ triggers
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MCDC Analyzer Skill                                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │ SKILL.md    │ →  │ analyze.py  │ →  │ mcdc-analyzer.agent.md  │ │
│  │ (triggers)  │    │ (parser)    │    │ (persona)               │ │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │ executes
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Static Analysis Engine (NO CODE EXECUTION)                         │
│  ┌──────────┐  ┌─────────────┐  ┌────────────┐  ┌───────────────┐  │
│  │AST Parser│→ │Condition    │→ │MCDC        │→ │Gap Detector   │  │
│  │          │  │Extractor    │  │Generator   │  │               │  │
│  └──────────┘  └─────────────┘  └────────────┘  └───────────────┘  │
│                                                                     │
│  Patterns: if/elif/else • .filter() • .where() • .when()           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Output                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │ MCDC Test Cases │  │ Logic Gaps      │  │ Negative Scenarios  │ │
│  │ (N+1 formula)   │  │ (missing paths) │  │ (NULL, boundary)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone this repo (or copy files)

```bash
git clone https://github.com/YOUR_USERNAME/mcdc-analyzer-skill.git
```

### 2. Copy to your project

```bash
# Copy the .github folder to your repo
cp -r mcdc-analyzer-skill/.github your-project/
```

Or for personal use (available in all projects):

```bash
# macOS/Linux
mkdir -p ~/.copilot/skills
cp -r .github/skills/mcdc-analyzer ~/.copilot/skills/

mkdir -p ~/.copilot/agents  
cp .github/agents/mcdc-analyzer.agent.md ~/.copilot/agents/
```

### 3. Open VS Code and ask Copilot

```
Analyze my PySpark code for MCDC coverage
```

That's it! 🎉

---

## 💬 Sample Conversation

See [docs/SAMPLE_CONVERSATION.md](docs/SAMPLE_CONVERSATION.md) for a complete example with screenshots.

**Quick Preview:**

**You:** `Analyze my PySpark code for MCDC coverage`

**Copilot:**
```
MCDC Analysis: sample_transformations.py

Decision 1: `df.filter(col("client_indicator") == "ES")`

Atomic condition:
  1. client_indicator == "ES"

MCDC test cases:
  • client_indicator = "ES" → included
  • client_indicator != "ES" / NULL → excluded

⚠️ Logic gaps:
  • Only handles "ES"
  • Missing coverage for "Y", "N", NULL, empty string
```

**You:** `Generate pytest test cases based on the MCDC analysis above`

**Copilot:** Creates `test_sample_transformations.py` with complete coverage tests!

---

## 📁 Repository Structure

```
.
├── .github/
│   ├── skills/
│   │   └── mcdc-analyzer/
│   │       ├── SKILL.md          # Skill definition & instructions
│   │       └── analyze.py        # Python AST analyzer script
│   └── agents/
│       └── mcdc-analyzer.agent.md  # Custom Copilot agent persona
├── docs/
│   ├── SAMPLE_CONVERSATION.md    # Full example with screenshots
│   └── MCDC_EXPLAINED.md         # What is MCDC?
├── examples/
│   └── sample_transformations.py # Sample PySpark code to test
├── README.md
└── LICENSE
```

---

## 🔍 What is MCDC?

**Modified Condition/Decision Coverage** is a code coverage criterion used in safety-critical systems (aviation, automotive, medical devices).

### The Key Insight

For a condition like `A and B and C`:
- **Multiple Condition Coverage (MCC)** = 2³ = **8 test cases** 😫
- **MCDC** = N+1 = **4 test cases** 🎯

### How MCDC Works

Each condition must **independently affect** the outcome:

| Test | A | B | C | Result | Purpose |
|------|---|---|---|--------|---------|
| 1 | T | T | T | **T** | Base case |
| 2 | **F** | T | T | **F** | A independence |
| 3 | T | **F** | T | **F** | B independence |
| 4 | T | T | **F** | **F** | C independence |

---

## 🛠️ Supported Patterns

### PySpark
```python
# ✅ .filter() / .where()
df.filter(col("status") == "ACTIVE")
df.where((col("amount") > 0) & (col("flag") == "Y"))

# ✅ .when() / .otherwise()
when(col("type") == "A", "Cat1").otherwise("Unknown")

# ✅ Complex boolean logic
df.filter((col("a") == 1) & ((col("b") > 10) | col("c").isNull()))
```

### Python
```python
# ✅ if/elif/else
if status == "pending" and amount > 0:
    process()

# ✅ Nested conditions
if client_type == "RETAIL":
    if amount > 5000:
        high_risk()
```

---

## ⚠️ Gap Detection

The analyzer finds these common issues:

| Gap Type | Example | Severity |
|----------|---------|----------|
| **Hardcoded values** | `== "ES"` without handling other codes | 🟡 Medium |
| **Missing NULL check** | No `.isNotNull()` before comparison | 🔴 High |
| **Boundary conditions** | `> 1000` vs `>= 1000` ambiguity | 🟢 Low |
| **Missing otherwise** | `when().when()` without `.otherwise()` | 🔴 High |
| **Incomplete branches** | `if/elif` without `else` | 🟡 Medium |

---

## 🧪 Running Standalone

You can also run the analyzer directly:

```bash
# Analyze a Python file
python .github/skills/mcdc-analyzer/analyze.py your_code.py

# Analyze a Jupyter notebook
python .github/skills/mcdc-analyzer/analyze.py notebook.ipynb

# Output as JSON (for CI/CD integration)
python .github/skills/mcdc-analyzer/analyze.py your_code.py --output json
```

---

## 🔗 Related Resources

- [GitHub Copilot Agent Skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [MCDC Coverage Explained](https://ldra.com/capabilities/mc-dc/)
- [NASA MCDC Tutorial](https://ntrs.nasa.gov/api/citations/20040086014/downloads/20040086014.pdf)
- [DO-178C Standard](https://en.wikipedia.org/wiki/DO-178C)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

<p align="center">
  <b>Built with ❤️ for data engineers who care about test coverage</b>
</p>
