from flask import Blueprint

bp = Blueprint('history', __name__)

from app.history import routes
