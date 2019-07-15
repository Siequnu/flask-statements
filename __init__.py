from flask import Blueprint

bp = Blueprint('statements', __name__)

from app.statements import routes, models, forms