from flask import render_template, url_for, flash, redirect, request, jsonify
from dashboard import dashboard
from models.transaction import Transaction
from models.category import Category
from models.budget import Budget
from models.notification import Notification
from extensions import db
from flask_login import login_required, current_user
from datetime import datetime, timezone

@dashboard.route("/")
@dashboard.route("/dashboard")
@login_required
def index():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()
    
    # Calculate totals
    all_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    total_income = sum(t.amount for t in all_transactions if t.type == 'income')
    total_expense = sum(t.amount for t in all_transactions if t.type == 'expense')
    total_balance = total_income - total_expense
    
    # Chart Data Preparation (Group by category for expenses)
    expense_data = {}
    for t in all_transactions:
        if t.type == 'expense':
            cat_name = t.category.name
            expense_data[cat_name] = expense_data.get(cat_name, 0) + t.amount

    # Get overall budget
    current_month = datetime.now(timezone.utc).month
    current_year = datetime.now(timezone.utc).year
    overall_budget = Budget.query.filter_by(user_id=current_user.id, category_id=None, month=current_month, year=current_year).first()

    return render_template('dashboard/index.html', title='Dashboard', 
                           recent_transactions=transactions,
                           total_balance=total_balance,
                           total_income=total_income,
                           total_expense=total_expense,
                           chart_labels=list(expense_data.keys()),
                           chart_values=list(expense_data.values()),
                           overall_budget=overall_budget)

@dashboard.route("/transactions", methods=['GET'])
@login_required
def transactions():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    categories = Category.query.all()
    return render_template('dashboard/transactions.html', title='Transactions', transactions=transactions, categories=categories)

@dashboard.route("/budgets", methods=['GET', 'POST'])
@login_required
def budgets():
    current_month = datetime.now(timezone.utc).month
    current_year = datetime.now(timezone.utc).year
    categories = Category.query.filter_by(type='expense').all()
    
    if request.method == 'POST':
        overall_limit = request.form.get('overall_limit')
        if overall_limit:
            budget = Budget.query.filter_by(user_id=current_user.id, category_id=None, month=current_month, year=current_year).first()
            if not budget:
                budget = Budget(user_id=current_user.id, category_id=None, month=current_month, year=current_year, monthly_limit=float(overall_limit))
                db.session.add(budget)
            else:
                budget.monthly_limit = float(overall_limit)
            
            # Recalculate spent for overall budget
            spent = sum(t.amount for t in Transaction.query.filter(Transaction.user_id==current_user.id, Transaction.type=='expense', db.extract('month', Transaction.date)==current_month, db.extract('year', Transaction.date)==current_year).all())
            budget.spent_amount = spent
            budget.remaining_amount = budget.monthly_limit - spent
            db.session.commit()
            flash('Overall budget updated!', 'success')
            
        # Handle category budgets
        for cat in categories:
            cat_limit = request.form.get(f'cat_limit_{cat.id}')
            if cat_limit:
                budget = Budget.query.filter_by(user_id=current_user.id, category_id=cat.id, month=current_month, year=current_year).first()
                if not budget:
                    budget = Budget(user_id=current_user.id, category_id=cat.id, month=current_month, year=current_year, monthly_limit=0, category_limit=float(cat_limit))
                    db.session.add(budget)
                else:
                    budget.category_limit = float(cat_limit)
                
                spent = sum(t.amount for t in Transaction.query.filter(Transaction.user_id==current_user.id, Transaction.type=='expense', Transaction.category_id==cat.id, db.extract('month', Transaction.date)==current_month, db.extract('year', Transaction.date)==current_year).all())
                budget.spent_amount = spent
                budget.remaining_amount = budget.category_limit - spent
        
        db.session.commit()
        return redirect(url_for('dashboard.budgets'))
        
    overall_budget = Budget.query.filter_by(user_id=current_user.id, category_id=None, month=current_month, year=current_year).first()
    category_budgets = Budget.query.filter(Budget.user_id==current_user.id, Budget.category_id!=None, Budget.month==current_month, Budget.year==current_year).all()
    cat_budgets_dict = {b.category_id: b for b in category_budgets}
    
    return render_template('dashboard/budget.html', title='Budgets', categories=categories, overall_budget=overall_budget, cat_budgets_dict=cat_budgets_dict)

def check_budget_alerts(user_id, category_id, amount):
    current_month = datetime.now(timezone.utc).month
    current_year = datetime.now(timezone.utc).year
    
    # Update Overall Budget
    overall_budget = Budget.query.filter_by(user_id=user_id, category_id=None, month=current_month, year=current_year).first()
    if overall_budget:
        overall_budget.spent_amount += amount
        overall_budget.remaining_amount = overall_budget.monthly_limit - overall_budget.spent_amount
        db.session.commit()
        
        pct = (overall_budget.spent_amount / overall_budget.monthly_limit) * 100
        if pct >= 100:
            db.session.add(Notification(user_id=user_id, message="You have exceeded your overall monthly budget limit!", alert_type="danger"))
        elif pct >= 80:
            db.session.add(Notification(user_id=user_id, message="Warning: You have used 80% of your overall monthly budget.", alert_type="warning"))
        elif pct >= 50:
            db.session.add(Notification(user_id=user_id, message="You have used 50% of your overall monthly budget.", alert_type="info"))

    # Update Category Budget
    cat_budget = Budget.query.filter_by(user_id=user_id, category_id=category_id, month=current_month, year=current_year).first()
    if cat_budget and cat_budget.category_limit:
        cat_budget.spent_amount += amount
        cat_budget.remaining_amount = cat_budget.category_limit - cat_budget.spent_amount
        db.session.commit()
        
        pct = (cat_budget.spent_amount / cat_budget.category_limit) * 100
        cat_name = Category.query.get(category_id).name
        if pct >= 100:
            db.session.add(Notification(user_id=user_id, message=f"Your {cat_name} expenses exceeded the limit!", alert_type="danger"))
        elif pct >= 80:
            db.session.add(Notification(user_id=user_id, message=f"{cat_name} budget almost finished (80% used).", alert_type="warning"))

    db.session.commit()

@dashboard.route("/transaction/add", methods=['POST'])
@login_required
def add_transaction():
    type = request.form.get('type')
    amount = float(request.form.get('amount'))
    category_id = int(request.form.get('category'))
    description = request.form.get('description')
    date_str = request.form.get('date')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now(timezone.utc)
    
    transaction = Transaction(
        user_id=current_user.id,
        category_id=category_id,
        type=type,
        amount=amount,
        description=description,
        date=date_obj
    )
    db.session.add(transaction)
    db.session.commit()
    
    if type == 'expense':
        check_budget_alerts(current_user.id, category_id, amount)
        
    flash('Transaction added successfully!', 'success')
    return redirect(url_for('dashboard.transactions'))

@dashboard.route("/transaction/<int:transaction_id>/delete", methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.author != current_user:
        flash('You do not have permission to delete this.', 'danger')
        return redirect(url_for('dashboard.transactions'))
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted!', 'success')
    return redirect(url_for('dashboard.transactions'))
