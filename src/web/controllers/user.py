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

    query = db.session.query(User).filter(User.id != current_user.id)

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
    roles = Rol.query.all()  # Añadir esta línea para pasar los roles a la vista
    return render_template("users/show.html", user=user, roles=roles)

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

@bp.route('/<int:user_id>/update_role', methods=['POST'])
@permiso_required('user_edit')
@login_required
def update_role(user_id):
    user = User.query.get_or_404(user_id)
    
    # Evitar que un usuario se edite a sí mismo
    if user.id == current_user.id:
        flash("No puedes modificarte a ti mismo.", "danger")
        return redirect(url_for("users.show", user_id=user.id))
    
    # Solo sysadmin puede editar roles
    if not current_user.es_sysadmin:
        flash("No tienes permisos para realizar esta acción.", "danger")
        return redirect(url_for("users.show", user_id=user.id))
    
    rol_id = request.form.get('rol_id')
    
    if rol_id == 'sysadmin':
        # Asignar administrador
        user.es_sysadmin = True
        user.rol = None  # Opcional: quitar rol si es administrador
        flash("Rol actualizado correctamente.", "success")
    elif rol_id:
        # Asignación de rol normal
        rol = Rol.query.get(rol_id)
        if rol:
            user.rol = rol
            user.es_sysadmin = False  # Quitar admin al asignar rol
            flash("Rol actualizado correctamente.", "success")
        else:
            flash("Rol no válido.", "danger")
    else:
        flash("Debes seleccionar una opción.", "danger")
    
    db.session.commit()
    return redirect(url_for("users.show", user_id=user.id))
