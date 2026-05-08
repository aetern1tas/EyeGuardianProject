from database import db, User
from gui import MainWindow
import os

def create_app():
    from flask import Flask
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eyeguard.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        user = User.query.first()
        if not user:
            user = User(username='default_user')
            db.session.add(user)
            db.session.commit()
            print(f"Создан пользователь: {user.username} (ID: {user.id})")
        
        return app, user

def main():
    print("Запуск EyeGuard Pro...")
    
    app, user = create_app()
    
    with app.app_context():
        window = MainWindow(db, user.id)
        window.run()

if __name__ == "__main__":
    main()