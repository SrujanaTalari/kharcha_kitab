"""
data_manager.py — Expense storage and retrieval using CSV
"""
import os
import pandas as pd
from datetime import date, datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "expenses.csv")

COLUMNS = ["id", "name", "amount", "category_en", "date", "note"]


def _ensure_file():
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)


def load_expenses() -> pd.DataFrame:
    _ensure_file()
    try:
        df = pd.read_csv(DATA_FILE, parse_dates=["date"])
        if df.empty:
            return pd.DataFrame(columns=COLUMNS)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    except Exception:
        return pd.DataFrame(columns=COLUMNS)


def save_expense(name: str, amount: float, category_en: str,
                 expense_date: date, note: str = "") -> None:
    _ensure_file()
    df = load_expenses()
    new_id = int(df["id"].max() + 1) if not df.empty else 1
    new_row = pd.DataFrame([{
        "id": new_id,
        "name": name,
        "amount": amount,
        "category_en": category_en,
        "date": expense_date,
        "note": note,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)


def delete_expense(expense_id: int) -> None:
    df = load_expenses()
    df = df[df["id"] != expense_id]
    df.to_csv(DATA_FILE, index=False)


def clear_all() -> None:
    pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)


def get_summary_for_ai(df: pd.DataFrame) -> str:
    """Build a plain-text expense summary to pass to the AI."""
    if df.empty:
        return "No expenses recorded yet."

    today = date.today()
    this_month = df[
        (pd.to_datetime(df["date"]).dt.month == today.month) &
        (pd.to_datetime(df["date"]).dt.year == today.year)
    ]

    lines = [f"Total expenses: {len(df)} entries"]
    lines.append(f"All-time total: ₹{df['amount'].sum():,.0f}")
    lines.append(f"This month total: ₹{this_month['amount'].sum():,.0f}")

    if not this_month.empty:
        cat_summary = this_month.groupby("category_en")["amount"].sum().sort_values(ascending=False)
        lines.append("\nThis month by category:")
        for cat, amt in cat_summary.items():
            lines.append(f"  {cat}: ₹{amt:,.0f}")

    lines.append("\nLast 10 expenses:")
    for _, row in df.sort_values("date", ascending=False).head(10).iterrows():
        lines.append(f"  {row['date']} | {row['name']} | ₹{row['amount']:,.0f} | {row['category_en']}")

    return "\n".join(lines)


def get_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    df2 = df.copy()
    df2["month"] = pd.to_datetime(df2["date"]).dt.to_period("M")
    trend = df2.groupby("month")["amount"].sum().reset_index()
    trend["month_str"] = trend["month"].astype(str)
    return trend
