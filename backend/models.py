# backend/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Ensure valid timestamp
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), default='')  # Default empty string to avoid NoneType

    def __repr__(self):
        return f'<Transaction {self.id}: ₹{self.amount} on {self.date.strftime("%Y-%m-%d")}>'


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False, unique=True)
    amount = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Budget {self.category}: ₹{self.amount}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<Category {self.name}>'
