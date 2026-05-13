from extensions import db

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    monthly_limit = db.Column(db.Float, nullable=False)
    category_limit = db.Column(db.Float, nullable=True)
    spent_amount = db.Column(db.Float, default=0.0)
    remaining_amount = db.Column(db.Float, default=0.0)
    month = db.Column(db.Integer, nullable=False) # e.g., 1-12
    year = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Budget('{self.user_id}', '{self.category_id}', '{self.monthly_limit}')"
