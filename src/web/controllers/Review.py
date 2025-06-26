from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user

from src.core.database import db
from src.core.Resenia.Review import Review

review_bp = Blueprint("review", __name__, url_prefix="/reviews")

@review_bp.route('/create/<int:rental_id>', methods=['POST'])
@login_required
def create(rental_id):
    stars = request.form.get("stars", type=int)
    comment = request.form.get("comment", "").strip()

    # Validación mínima
    if not stars or stars < 1 or stars > 5:
        flash("Debe ingresar una puntuación válida entre 1 y 5 estrellas.", "danger")
        return redirect(url_for("rental.show", rental_id=rental_id))

    review = Review(
        stars=stars,
        comment=comment if comment else None,
        user_id=current_user.id,
        rental_id=rental_id
    )

    db.session.add(review)
    db.session.commit()

    flash("Reseña guardada con éxito", "success")
    return redirect(url_for("rental.show", rental_id=rental_id))

@review_bp.route('/<int:review_id>/delete', methods=['POST'])
@login_required
def delete(review_id):
    review = Review.query.get_or_404(review_id)

    if review.user_id != current_user.id:
        flash("No tenés permiso para eliminar esta reseña.", "danger")
        return redirect(url_for('rental.show', rental_id=request.args.get('rental_id')))

    rental_id = review.rental_id
    db.session.delete(review)
    db.session.commit()
    flash("Reseña borrada con éxito", "success")
    return redirect(url_for('rental.show', rental_id=rental_id))