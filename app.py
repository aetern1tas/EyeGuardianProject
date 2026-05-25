from flask import Flask
from config import Config
from database.models import db, User
from services.session_service import create_session, end_session
from gui.main_window import MainWindow
from utils.logger import logger

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        user = User.query.first()
        if not user:
            user = User(username='default_user')
            db.session.add(user)
            db.session.commit()
            logger.info(f'Created user: {user.username}')
    return app, user

def main():
    logger.info('Starting EyeGuard Pro...')
    app, user = create_app()
    with app.app_context():
        session = create_session(user.id)
        try:
            window = MainWindow(
                user_id=user.id,
                session_id=session.id,
                session_obj=session
            )
            window.run()
        finally:
            end_session(session)
            logger.info('Session ended')

if __name__ == '__main__':
    main()