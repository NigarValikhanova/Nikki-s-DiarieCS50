import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key'
    DATABASE = os.path.join(BASE_DIR, 'diary.db')


UPLOAD_FOLDER = 'static/images/gallery'
