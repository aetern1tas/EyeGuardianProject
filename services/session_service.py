from database.models import db, Session
from datetime import datetime

def create_session(user_id):
    session = Session(user_id=user_id)
    db.session.add(session)
    db.session.commit()
    return session

def end_session(session):
    session.end_time = datetime.utcnow()
    duration = session.end_time - session.start_time
    session.total_minutes = int(duration.total_seconds() // 60)
    db.session.commit()

