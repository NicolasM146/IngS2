from flask import render_template, url_for
from flask_mail import Message

from src.utils.token import generate_confirmation_token, confirm_token

def send_email(subject, recipient, html_body):
    from src.web import mail
    msg = Message(subject, recipients=[recipient])
    msg.html = html_body
    mail.send(msg)

def send_confirmation_email(email):
    token = generate_confirmation_token(email)
    confirm_url = url_for('register.confirm_email', token=token, _external=True)
    html = render_template('email/confirm.html', confirm_url=confirm_url)
    send_email("Confirma tu cuenta en Alquilando", email, html)

def send_password_reset_email(email, token):
    subject = "Restablecer tu contraseña en Alquilando"
    reset_url = url_for('login.reset_password', token=token, _external=True)
    html = render_template('email/reset_password.html', reset_url=reset_url)
    send_email(subject, email, html)

