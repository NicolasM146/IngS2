from flask import render_template, url_for, current_app
from flask_mail import Message
from src.utils.token import generate_confirmation_token

def send_confirmation_email(user_email):
    from src.web import mail  # Import dentro de la función para evitar import circular
    token = generate_confirmation_token(user_email)
    confirm_url = url_for('register.confirm_email', token=token, _external=True)
    html = render_template('email/confirm.html', confirm_url=confirm_url)
    msg = Message('Por favor confirma tu email', sender=current_app.config['MAIL_USERNAME'], recipients=[user_email])
    msg.html = html
    mail.send(msg)
