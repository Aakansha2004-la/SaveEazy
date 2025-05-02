# backend/finance.py

from models import Transaction, Budget, db
from sqlalchemy import func
import calendar
from datetime import datetime
from collections import defaultdict
from dateutil.relativedelta import relativedelta


def calculate_budget_summary():
    """Calculate budget vs actual spending."""
    budgets = {b.category: b.amount for b in Budget.query.all()}
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    start_date = datetime(current_year, current_month, 1)
    last_day = calendar.monthrange(current_year, current_month)[1]
    end_date = datetime(current_year, current_month, last_day)
    
    spending_by_category = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total_spent')
    ).filter(
        Transaction.date.between(start_date, end_date)
    ).group_by(
        Transaction.category
    ).all()
    
    spending = {category: float(total_spent) for category, total_spent in spending_by_category}
    
    summary = {
        'month': calendar.month_name[current_month],
        'year': current_year,
        'categories': []
    }
    
    total_budget = 0
    total_spent = 0
    
    for category, budget_amount in budgets.items():
        spent = spending.get(category, 0.0)
        remaining = budget_amount - spent
        percent_used = (spent / budget_amount * 100) if budget_amount > 0 else 0
        
        summary['categories'].append({
            'category': category,
            'budget': budget_amount,
            'spent': spent,
            'remaining': remaining,
            'percent_used': percent_used
        })
        
        total_budget += budget_amount
        total_spent += spent
    
    for category, spent in spending.items():
        if category not in budgets:
            summary['categories'].append({
                'category': category,
                'budget': 0,
                'spent': spent,
                'remaining': -spent,
                'percent_used': float('inf')
            })
            total_spent += spent
    
    summary['total_budget'] = total_budget
    summary['total_spent'] = total_spent
    summary['total_remaining'] = total_budget - total_spent
    summary['overall_percent_used'] = (total_spent / total_budget * 100) if total_budget > 0 else 0
    
    return summary


def analyze_spending_patterns():
    """Analyze spending patterns over time for charts."""
    six_months_ago = datetime.now() - relativedelta(months=6)
    transactions = Transaction.query.filter(Transaction.date >= six_months_ago).all()

    monthly_spending = defaultdict(lambda: defaultdict(float))
    category_totals = defaultdict(float)

    for transaction in transactions:
        month_key = f"{transaction.date.year}-{transaction.date.month:02d}"
        monthly_spending[month_key][transaction.category] += transaction.amount
        category_totals[transaction.category] += transaction.amount

    months = sorted(monthly_spending.keys())
    categories = sorted(category_totals.keys())

    by_date = []
    for month in months:
        by_date.append({
            "month": month,
            "spending": [monthly_spending[month].get(category, 0) for category in categories]
        })

    by_category = [{"category": cat, "total": category_totals[cat]} for cat in categories]

    return {
        "by_date": by_date,
        "by_category": by_category
    }

