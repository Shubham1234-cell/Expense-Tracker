from extensions import db

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    currency = db.Column(db.String(10), default='USD')
    theme = db.Column(db.String(10), default='light')
    email_notifications = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"Setting('{self.user_id}', '{self.currency}', '{self.theme}')"
