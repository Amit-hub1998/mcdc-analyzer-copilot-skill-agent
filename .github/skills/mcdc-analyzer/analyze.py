#!/usr/bin/env python3
"""
MCDC Code Analyzer - Static Analysis for PySpark/Python Code

This script analyzes code WITHOUT executing it, using Python's AST module.
It identifies conditions, generates MCDC test cases, and finds logic gaps.

Usage:
    python analyze.py <file.py or file.ipynb>
    python analyze.py <file.py> --output json
    python analyze.py <file.py> --output markdown
"""

import ast
import json
import sys
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
from itertools import combinations


@dataclass
class AtomicCondition:
    """A single atomic condition within a decision."""
    text: str
    variables: List[str]
    operator: Optional[str] = None  # ==, >, <, >=, <=, !=, is, in
    compared_value: Optional[str] = None


@dataclass
class Decision:
    """A decision point containing one or more atomic conditions."""
    line_number: int
    source_text: str
    decision_type: str  # 'if', 'filter', 'when', 'where'
    atomic_conditions: List[AtomicCondition] = field(default_factory=list)
    boolean_operators: List[str] = field(default_factory=list)  # 'and', 'or'


@dataclass
class MCDCTestCase:
    """A single MCDC test case."""
    case_number: int
    variable_values: Dict[str, str]
    expected_result: bool
    purpose: str


@dataclass
class LogicGap:
    """A detected logic gap in the code."""
    gap_type: str
    description: str
    severity: str  # 'high', 'medium', 'low'
    suggestion: str


@dataclass
class AnalysisResult:
    """Complete analysis result for a decision."""
    decision: Decision
    mcdc_test_cases: List[MCDCTestCase] = field(default_factory=list)
    logic_gaps: List[LogicGap] = field(default_factory=list)
    negative_scenarios: List[Dict] = field(default_factory=list)


class ConditionExtractor(ast.NodeVisitor):
    """Extract conditions from Python/PySpark code using AST."""
    
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.decisions: List[Decision] = []
        
    def get_source_segment(self, node) -> str:
        """Get the source code for a node."""
        try:
            return ast.unparse(node)
        except:
            if hasattr(node, 'lineno'):
                return self.source_lines[node.lineno - 1].strip()
            return "<unknown>"
    
    def extract_atomic_conditions(self, node) -> Tuple[List[AtomicCondition], List[str]]:
        """Recursively extract atomic conditions and boolean operators."""
        conditions = []
        operators = []
        
        if isinstance(node, ast.BoolOp):
            # Handle 'and' / 'or'
            op_name = 'and' if isinstance(node.op, ast.And) else 'or'
            for i, value in enumerate(node.values):
                sub_conds, sub_ops = self.extract_atomic_conditions(value)
                conditions.extend(sub_conds)
                operators.extend(sub_ops)
                if i < len(node.values) - 1:
                    operators.append(op_name)
                    
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            # Handle 'not'
            sub_conds, sub_ops = self.extract_atomic_conditions(node.operand)
            for cond in sub_conds:
                cond.text = f"not ({cond.text})"
            conditions.extend(sub_conds)
            operators.extend(sub_ops)
            
        elif isinstance(node, ast.Compare):
            # Atomic comparison: a == b, x > 10, etc.
            variables = self._extract_variables(node)
            op_symbols = {
                ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=',
                ast.Gt: '>', ast.GtE: '>=', ast.Is: 'is', ast.IsNot: 'is not',
                ast.In: 'in', ast.NotIn: 'not in'
            }
            op = op_symbols.get(type(node.ops[0]), '?') if node.ops else None
            compared = self.get_source_segment(node.comparators[0]) if node.comparators else None
            
            conditions.append(AtomicCondition(
                text=self.get_source_segment(node),
                variables=variables,
                operator=op,
                compared_value=compared
            ))
            
        elif isinstance(node, ast.Call):
            # Handle method calls like col("x").isNull(), df.filter(...)
            conditions.append(AtomicCondition(
                text=self.get_source_segment(node),
                variables=self._extract_variables(node)
            ))
            
        elif isinstance(node, ast.Name):
            # Simple variable as condition: if flag:
            conditions.append(AtomicCondition(
                text=node.id,
                variables=[node.id]
            ))
            
        else:
            # Fallback: treat entire node as one condition
            conditions.append(AtomicCondition(
                text=self.get_source_segment(node),
                variables=self._extract_variables(node)
            ))
            
        return conditions, operators
    
    def _extract_variables(self, node) -> List[str]:
        """Extract all variable names from a node."""
        variables = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                variables.append(child.id)
            elif isinstance(child, ast.Attribute):
                # Handle col("x") or df.column
                full_name = self.get_source_segment(child)
                variables.append(full_name)
            elif isinstance(child, ast.Constant) and isinstance(child.value, str):
                # Extract string literals used as column names
                if child.value and not child.value.startswith(('_', '.')):
                    pass  # Don't add string constants as variables
        return list(set(variables))
    
    def visit_If(self, node):
        """Extract conditions from if statements."""
        conditions, operators = self.extract_atomic_conditions(node.test)
        
        decision = Decision(
            line_number=node.lineno,
            source_text=self.get_source_segment(node.test),
            decision_type='if',
            atomic_conditions=conditions,
            boolean_operators=operators
        )
        self.decisions.append(decision)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Extract conditions from PySpark filter/when/where calls."""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            
            if method_name in ('filter', 'where') and node.args:
                conditions, operators = self.extract_atomic_conditions(node.args[0])
                decision = Decision(
                    line_number=node.lineno,
                    source_text=self.get_source_segment(node.args[0]),
                    decision_type=method_name,
                    atomic_conditions=conditions,
                    boolean_operators=operators
                )
                self.decisions.append(decision)
                
            elif method_name == 'when' and node.args:
                conditions, operators = self.extract_atomic_conditions(node.args[0])
                decision = Decision(
                    line_number=node.lineno,
                    source_text=self.get_source_segment(node.args[0]),
                    decision_type='when',
                    atomic_conditions=conditions,
                    boolean_operators=operators
                )
                self.decisions.append(decision)
                
        self.generic_visit(node)


class MCDCGenerator:
    """Generate MCDC test cases for a decision."""
    
    def generate(self, decision: Decision) -> List[MCDCTestCase]:
        """Generate N+1 test cases for N atomic conditions."""
        n = len(decision.atomic_conditions)
        if n == 0:
            return []
            
        test_cases = []
        
        # Determine dominant operator (simplified - real MCDC is more complex)
        has_and = 'and' in decision.boolean_operators
        has_or = 'or' in decision.boolean_operators
        
        # Base case: all conditions make decision true
        base_values = {}
        for i, cond in enumerate(decision.atomic_conditions):
            var_name = f"cond_{i+1}"
            base_values[cond.text] = "TRUE"
            
        test_cases.append(MCDCTestCase(
            case_number=1,
            variable_values=base_values.copy(),
            expected_result=True,
            purpose="Base case - all conditions TRUE"
        ))
        
        # For each condition, flip it to show independence
        for i, cond in enumerate(decision.atomic_conditions):
            flipped = base_values.copy()
            flipped[cond.text] = "FALSE"
            
            # Expected result depends on operators
            if has_and and not has_or:
                expected = False
            elif has_or and not has_and:
                expected = True if i > 0 else False
            else:
                expected = False  # Mixed - conservative
                
            test_cases.append(MCDCTestCase(
                case_number=i + 2,
                variable_values=flipped,
                expected_result=expected,
                purpose=f"Tests independence of: {cond.text[:50]}"
            ))
            
        return test_cases


class LogicGapDetector:
    """Detect common logic gaps in conditions."""
    
    def detect(self, decision: Decision) -> List[LogicGap]:
        """Find logic gaps in a decision."""
        gaps = []
        
        for cond in decision.atomic_conditions:
            # Check for hardcoded string comparisons
            if cond.operator == '==' and cond.compared_value:
                if cond.compared_value.startswith(("'", '"')):
                    gaps.append(LogicGap(
                        gap_type="hardcoded_value",
                        description=f"Condition checks for specific value {cond.compared_value}",
                        severity="medium",
                        suggestion=f"What about other values? Consider: NULL, empty string, other valid codes"
                    ))
            
            # Check for missing null handling
            if not any('null' in v.lower() or 'none' in v.lower() 
                      for v in cond.variables):
                if 'isNull' not in cond.text and 'isNotNull' not in cond.text:
                    gaps.append(LogicGap(
                        gap_type="missing_null_check",
                        description=f"No NULL check for variables in: {cond.text[:50]}",
                        severity="high",
                        suggestion="Add explicit NULL handling or document expected behavior"
                    ))
            
            # Check for boundary conditions
            if cond.operator in ('>', '<'):
                gaps.append(LogicGap(
                    gap_type="boundary_condition",
                    description=f"Strict inequality '{cond.operator}' - boundary value not covered",
                    severity="low",
                    suggestion=f"Test with exact boundary value. Is '{cond.operator}' or '{cond.operator}=' intended?"
                ))
        
        # Check for missing else/otherwise
        if decision.decision_type == 'when':
            gaps.append(LogicGap(
                gap_type="potential_missing_otherwise",
                description="PySpark when() detected - verify .otherwise() exists",
                severity="medium",
                suggestion="Ensure there's an .otherwise() clause to handle unmatched cases"
            ))
            
        return gaps


class NegativeScenarioGenerator:
    """Generate negative test scenarios."""
    
    def generate(self, decision: Decision) -> List[Dict]:
        """Generate edge case scenarios."""
        scenarios = []
        
        # Get unique variables
        all_vars = set()
        for cond in decision.atomic_conditions:
            all_vars.update(cond.variables)
        
        # Generate scenarios for each variable
        for var in all_vars:
            if 'col(' in var or any(c.isupper() for c in var):
                # Likely a column reference
                scenarios.extend([
                    {"variable": var, "value": "NULL", "scenario": "Null value"},
                    {"variable": var, "value": "''", "scenario": "Empty string"},
                    {"variable": var, "value": "' '", "scenario": "Whitespace only"},
                ])
            
            # Check if numeric comparison
            for cond in decision.atomic_conditions:
                if var in cond.variables and cond.operator in ('>', '<', '>=', '<='):
                    scenarios.extend([
                        {"variable": var, "value": "0", "scenario": "Zero value"},
                        {"variable": var, "value": "-1", "scenario": "Negative value"},
                        {"variable": var, "value": "NULL", "scenario": "Null numeric"},
                    ])
                    break
                    
        return scenarios


def parse_jupyter_notebook(filepath: Path) -> str:
    """Extract Python code from a Jupyter notebook."""
    with open(filepath, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    code_cells = []
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') == 'code':
            source = cell.get('source', [])
            if isinstance(source, list):
                code_cells.append(''.join(source))
            else:
                code_cells.append(source)
    
    return '\n\n'.join(code_cells)


def analyze_code(code: str) -> List[AnalysisResult]:
    """Analyze code and return all results."""
    source_lines = code.split('\n')
    
    # Parse AST
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"Syntax error in code: {e}")
        return []
    
    # Extract conditions
    extractor = ConditionExtractor(source_lines)
    extractor.visit(tree)
    
    # Analyze each decision
    mcdc_gen = MCDCGenerator()
    gap_detector = LogicGapDetector()
    scenario_gen = NegativeScenarioGenerator()
    
    results = []
    for decision in extractor.decisions:
        result = AnalysisResult(
            decision=decision,
            mcdc_test_cases=mcdc_gen.generate(decision),
            logic_gaps=gap_detector.detect(decision),
            negative_scenarios=scenario_gen.generate(decision)
        )
        results.append(result)
    
    return results


def format_markdown_report(results: List[AnalysisResult]) -> str:
    """Format results as Markdown."""
    lines = ["# MCDC Analysis Report\n"]
    lines.append(f"**Total Decisions Analyzed:** {len(results)}\n")
    
    for i, result in enumerate(results, 1):
        d = result.decision
        lines.append(f"\n## Decision {i}: Line {d.line_number} ({d.decision_type})\n")
        lines.append(f"**Code:** `{d.source_text[:100]}`\n")
        
        # Atomic conditions
        lines.append(f"\n### Atomic Conditions ({len(d.atomic_conditions)})\n")
        for j, cond in enumerate(d.atomic_conditions, 1):
            lines.append(f"{j}. `{cond.text}`")
            if cond.operator:
                lines.append(f"   - Operator: `{cond.operator}`")
            if cond.variables:
                lines.append(f"   - Variables: {', '.join(cond.variables)}")
        
        # MCDC Test Cases
        lines.append(f"\n### MCDC Test Cases (N+1 = {len(result.mcdc_test_cases)})\n")
        lines.append("| # | Condition Values | Expected | Purpose |")
        lines.append("|---|-----------------|----------|---------|")
        for tc in result.mcdc_test_cases:
            vals = ', '.join(f"{k[:20]}={v}" for k, v in tc.variable_values.items())
            lines.append(f"| {tc.case_number} | {vals[:40]} | {tc.expected_result} | {tc.purpose[:30]} |")
        
        # Logic Gaps
        if result.logic_gaps:
            lines.append(f"\n### ⚠️ Logic Gaps Detected ({len(result.logic_gaps)})\n")
            for gap in result.logic_gaps:
                icon = "🔴" if gap.severity == "high" else "🟡" if gap.severity == "medium" else "🟢"
                lines.append(f"{icon} **{gap.gap_type}**: {gap.description}")
                lines.append(f"   - 💡 {gap.suggestion}\n")
        
        # Negative Scenarios
        if result.negative_scenarios:
            lines.append(f"\n### Negative Test Scenarios\n")
            lines.append("| Variable | Test Value | Scenario |")
            lines.append("|----------|------------|----------|")
            for scenario in result.negative_scenarios[:10]:  # Limit output
                lines.append(f"| {scenario['variable'][:20]} | {scenario['value']} | {scenario['scenario']} |")
    
    return '\n'.join(lines)


def format_json_report(results: List[AnalysisResult]) -> str:
    """Format results as JSON."""
    output = []
    for result in results:
        output.append({
            "decision": {
                "line_number": result.decision.line_number,
                "source_text": result.decision.source_text,
                "type": result.decision.decision_type,
                "atomic_conditions": [asdict(c) for c in result.decision.atomic_conditions],
                "boolean_operators": result.decision.boolean_operators
            },
            "mcdc_test_cases": [asdict(tc) for tc in result.mcdc_test_cases],
            "logic_gaps": [asdict(g) for g in result.logic_gaps],
            "negative_scenarios": result.negative_scenarios
        })
    return json.dumps(output, indent=2)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <file.py or file.ipynb> [--output json|markdown]")
        print("\nThis tool analyzes Python/PySpark code for MCDC coverage gaps.")
        print("It does NOT execute the code - pure static analysis only.")
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    output_format = 'markdown'
    
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1]
    
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    # Read code
    if filepath.suffix == '.ipynb':
        code = parse_jupyter_notebook(filepath)
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
    
    # Analyze
    results = analyze_code(code)
    
    if not results:
        print("No decisions (if/filter/when statements) found in the code.")
        sys.exit(0)
    
    # Output
    if output_format == 'json':
        print(format_json_report(results))
    else:
        print(format_markdown_report(results))


if __name__ == '__main__':
    main()
