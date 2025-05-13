from flask import render_template, request, Blueprint
from src.core.Usuario.User import User
from src.core.database import db
from flask import flash, redirect, url_for
from sqlalchemy.orm import Session
from datetime import datetime

bp = Blueprint("users", __name__, url_prefix="/usuarios")

session = Session()

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    users_query = User.query.order_by(User.id.desc())
    total = users_query.count()
    users = users_query.offset((page - 1) * per_page).limit(per_page).all()

    no_results = len(users) == 0

    return render_template('users/index.html', 
                       users=users, 
                       no_results=no_results, 
                       page=page, 
                       total=total, 
                       per_page=per_page)

