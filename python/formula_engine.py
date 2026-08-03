from __future__ import annotations

import ast
from dataclasses import dataclass

import numpy as np


ALIASES = {
    "Fc": "Fc", "U": "U", "I": "I", "Er": "Er", "theta_red": "theta_red",
    "t": "t", "Fr": "Fr", "Dch": "Dch", "Vch": "Vch",
    "theta_m": "theta_m", "omega_m": "omega_m", "omega_red": "omega_red",
}

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)


@dataclass(frozen=True)
class FormulaDefinition:
    expression: str
    label: str = "Formule"
    unit: str = ""


def validate_formula(expression: str) -> ast.Expression:
    text = expression.strip().replace("×", "*").replace("÷", "/").replace("−", "-")
    if not text:
        raise ValueError("La formule est vide.")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise ValueError("La formule n'est pas syntaxiquement correcte.") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Expression | ast.Load | ast.Constant):
            continue
        if isinstance(node, ast.Name):
            if node.id not in ALIASES:
                raise ValueError(f"Grandeur inconnue : {node.id}")
            continue
        if isinstance(node, ast.BinOp):
            if not isinstance(node.op, _ALLOWED_BINOPS):
                raise ValueError("Opérateur non autorisé.")
            continue
        if isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, _ALLOWED_UNARY):
                raise ValueError("Opérateur unaire non autorisé.")
            continue
        if isinstance(node, _ALLOWED_BINOPS + _ALLOWED_UNARY):
            continue
        raise ValueError("La formule contient un élément non autorisé.")
    return tree


def evaluate_formula(expression: str, values: dict[str, np.ndarray]) -> np.ndarray:
    tree = validate_formula(expression)

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError("Seules les constantes numériques sont autorisées.")
            return float(node.value)
        if isinstance(node, ast.Name):
            return np.asarray(values[ALIASES[node.id]], dtype=float)
        if isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left, right = evaluate(node.left), evaluate(node.right)
            with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                if isinstance(node.op, ast.Add): return left + right
                if isinstance(node.op, ast.Sub): return left - right
                if isinstance(node.op, ast.Mult): return left * right
                if isinstance(node.op, ast.Div): return left / right
                if isinstance(node.op, ast.Pow): return left ** right
        raise ValueError("Élément de formule non pris en charge.")

    result = np.asarray(evaluate(tree), dtype=float)
    if result.ndim == 0:
        sample = next(iter(values.values()))
        result = np.full_like(np.asarray(sample, dtype=float), float(result))
    return result
