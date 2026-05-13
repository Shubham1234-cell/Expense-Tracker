from extensions import db
from datetime import datetime, timezone

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False) # 'expense' or 'income'
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    receipt_image = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"Transaction('{self.type}', '{self.amount}', '{self.date}')"
