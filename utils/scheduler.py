from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone
from utils.email_service import send_weekly_report
from models.user import User
from models.transaction import Transaction
import atexit

scheduler = BackgroundScheduler()

def weekly_report_job(app):
    with app.app_context():
        # Get last 7 days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        users = User.query.filter_by(is_verified=True).all()
        for user in users:
            transactions = Transaction.query.filter(
                Transaction.user_id == user.id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).all()
            
            total_expense = sum(t.amount for t in transactions if t.type == 'expense')
            total_income = sum(t.amount for t in transactions if t.type == 'income')
            
            # Find highest spending category
            expense_data = {}
            for t in transactions:
                if t.type == 'expense':
                    cat_name = t.category.name
                    expense_data[cat_name] = expense_data.get(cat_name, 0) + t.amount
                    
            highest_category = max(expense_data.items(), key=lambda x: x[1])[0] if expense_data else "None"
            
            send_weekly_report(user, start_date, end_date, total_expense, total_income, highest_category, expense_data)

def init_scheduler(app):
    # Pass app context to the job
    scheduler.add_job(func=weekly_report_job, args=[app], trigger="interval", days=7, id='weekly_report')
    scheduler.start()
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
