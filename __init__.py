from flask import Blueprint

bp = Blueprint('statements', __name__, template_folder = 'templates')

from app.statements import routes, models, forms