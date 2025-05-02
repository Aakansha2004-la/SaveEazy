# backend/app.py
from flask import Flask, request, jsonify
from models import db, Transaction, Budget, Category
from finance import calculate_budget_summary, analyze_spending_patterns
import requests
import os
import logging
from flask_cors import CORS
from datetime import datetime


app = Flask(__name__)
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:8501"}})  # Restrict in production
CORS(app)  # Allow all origins for development

# Logging
logging.basicConfig(level=logging.INFO)

# Configure SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'finance.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def home():
    return "Backend working"

# Transactions Routes
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    transactions = Transaction.query.all()
    return jsonify([{
        'id': t.id,
        'date': t.date.isoformat(),
        'amount': t.amount,
        'category': t.category,
        'description': t.description
    } for t in transactions])

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    try:
        data = request.json
        logging.info(f"Received transaction data: {data}")

        # Input validation
        if 'amount' not in data or 'category' not in data or 'date' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            try:
                date_obj = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            except ValueError:
                date_obj = datetime.utcnow()

        transaction = Transaction(
            date=date_obj,
            amount=float(data['amount']),
            category=data['category'],
            description=data.get('description', '')
        )

        db.session.add(transaction)
        db.session.commit()
        return jsonify({'id': transaction.id}), 201

    except Exception as e:
        logging.error(f"Error adding transaction: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    transaction = Transaction.query.get(transaction_id)
    if transaction:
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({'message': 'Transaction deleted'})
    return jsonify({'error': 'Transaction not found'}), 404

@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    data = request.json

    if 'amount' in data:
        transaction.amount = float(data['amount'])
    if 'category' in data:
        transaction.category = data['category']
    if 'description' in data:
        transaction.description = data['description']
    if 'date' in data:
        try:
            transaction.date = datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            transaction.date = datetime.utcnow()

    db.session.commit()
    return jsonify({'message': 'Transaction updated'})

# Budget Routes
@app.route('/api/budget', methods=['GET'])
def get_budget():
    budget_items = Budget.query.all()
    return jsonify([{
        'id': b.id,
        'category': b.category,
        'amount': b.amount
    } for b in budget_items])

@app.route('/api/budget', methods=['POST'])
def set_budget():
    data = request.json
    if 'budgets' not in data:
        return jsonify({'error': 'Missing budgets list'}), 400

    try:
        for item in data['budgets']:
            category = item['category']
            amount = float(item['budget'])

            budget_item = Budget.query.filter_by(category=category).first()
            if budget_item:
                budget_item.amount = amount
            else:
                budget_item = Budget(category=category, amount=amount)
                db.session.add(budget_item)

        db.session.commit()
        return jsonify({'message': 'Budgets updated'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/budget/<int:budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    budget_item = Budget.query.get(budget_id)
    if budget_item:
        db.session.delete(budget_item)
        db.session.commit()
        return jsonify({'message': 'Budget item deleted'})
    return jsonify({'error': 'Budget item not found'}), 404

# Categories Routes
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([c.name for c in categories])

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.json
    if 'name' not in data:
        return jsonify({'error': 'Missing category name'}), 400
    category = Category(name=data['name'])
    db.session.add(category)
    db.session.commit()
    return jsonify({'id': category.id}), 201

# Analysis Routes
@app.route('/api/analysis/budget_summary', methods=['GET'])
def budget_summary():
    return jsonify(calculate_budget_summary())

@app.route('/api/analysis/spending_patterns', methods=['GET'])
def spending_patterns():
    return jsonify(analyze_spending_patterns())

# Initialize database with default categories
with app.app_context():
    db.create_all()
    if Category.query.count() == 0:
        default_categories = [
            "Housing", "Transportation", "Food", "Utilities",
            "Insurance", "Healthcare", "Savings", "Debt",
            "Personal", "Recreation", "Miscellaneous"
        ]
        for category_name in default_categories:
            db.session.add(Category(name=category_name))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

