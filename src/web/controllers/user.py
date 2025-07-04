from flask import render_template, request, Blueprint
from src.core.Usuario.User import User
from src.core.database import db
from flask import flash, redirect, url_for
from sqlalchemy.orm import Session
from datetime import datetime
from flask_login import login_required, current_user
from src.web.handlers.auth import permiso_required
from src.core.Usuario.Roles_y_Permisos import Rol

bp = Blueprint("users", __name__, url_prefix="/usuarios")

session = Session()

@bp.route('/')
@permiso_required('user_index')
@login_required
def index():
    nombre = request.args.get('nombre')
    email = request.args.get('email')
    rol = request.args.get('rol')
    estado = request.args.get('estado')
    page = int(request.args.get('page', 1))
    per_page = 10

    query = db.session.query(User)

    if nombre:
        query = query.filter(User.nombre.ilike(f'%{nombre}%'))
    if email:
        query = query.filter(User.email.ilike(f'%{email}%'))
    if rol:
        query = query.join(User.rol).filter(Rol.nombre == rol)
    if estado == 'activo':
        query = query.filter(User.is_locked == False)
    elif estado == 'bloqueado':
        query = query.filter(User.is_locked == True)

    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()
    no_results = total == 0

    return render_template('users/index.html',
                           users=users,
                           page=page,
                           per_page=per_page,
                           total=total,
                           no_results=no_results)
    

@bp.route('/<int:user_id>', endpoint="show")
@permiso_required('user_show')
@login_required
def show(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("users/show.html", user=user)

@bp.route('/<int:user_id>/lock')
@permiso_required('user_edit')
@login_required
def lock(user_id):
    user = User.query.get_or_404(user_id)
    user.bloquear()
    db.session.commit()
    flash(f"Usuario {user.nombre} bloqueado.", "warning")
    return redirect(url_for("users.show", user_id=user.id))

@bp.route('/<int:user_id>/unlock')
@permiso_required('user_edit')
@login_required
def unlock(user_id):
    user = User.query.get_or_404(user_id)
    user.desbloquear()
    db.session.commit()
    flash(f"Usuario {user.nombre} desbloqueado.", "success")
    return redirect(url_for("users.show", user_id=user.id))