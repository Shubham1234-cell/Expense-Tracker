from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from extensions import db, login_manager, migrate, bcrypt, mail
from config import Config
from utils.scheduler import init_scheduler

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    mail.init_app(app)
    
    init_scheduler(app)

    from models import User, Category, Transaction, Budget, Notification, Setting
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from dashboard.routes import dashboard as dashboard_blueprint
    app.register_blueprint(dashboard_blueprint)

    from admin.routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    return app

    app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default categories if none exist
        from models.category import Category
        if not Category.query.first():
            default_categories = ['Food', 'Travel', 'Shopping', 'Entertainment', 'Bills', 'Education', 'Health', 'Investment', 'Others']
            for name in default_categories:
                db.session.add(Category(name=name, type='expense'))
            db.session.add(Category(name='Salary', type='income'))
            db.session.commit()
    app.run(debug=True)
