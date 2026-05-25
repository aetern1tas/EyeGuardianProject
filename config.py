import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'eyeguard.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EAR_THRESHOLD = 0.21
    CONSECUTIVE_FRAMES = 3