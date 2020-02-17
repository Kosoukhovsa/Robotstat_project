import os
import secrets

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    #SECRET_KEY = open('/path/to/secret/file').read()
    SECRET_KEY = SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_urlsafe(16))
    #os.environ.get('SECRET_KEY', 'my_secret_key_@!@%@^%!^12212')
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = os.environ.get('MAIL_PORT', '587')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'robotstatmail@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'rg$5J8YqvR')
    #FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    #FLASKY_MAIL_SENDER = 'Flasky Admin <robotstatmail@gmail.com>'
    MAIL_ADMIN = os.environ.get('MAIL_ADMIN','ikpservicemail@gmail.com')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'robot-dev.sqlite')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
    'sqlite://'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = \
    'postgres://gnmdxxghdjocyl:23b32feeec55d523f962ed6c3aa479d77dd4dbf9e0a29525064acc8d4c00fabc@ec2-54-75-245-196.eu-west-1.compute.amazonaws.com:5432/d7vdphdfdo26vj'

config = {
'development': DevelopmentConfig,
'testing': TestingConfig,
'production': ProductionConfig,
'default': DevelopmentConfig
}
