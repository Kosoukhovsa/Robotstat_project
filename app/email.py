from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from app import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, template, **kwargs):
    # recipients - список
    app = current_app._get_current_object()
    msg = Message(app.config['IKP_MAIL_SUBJECT_PREFIX'] + subject,
                    sender=app.config['MAIL_USERNAME'],
                    recipients=recipients)
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    #mail.send(msg)
    thr=Thread(target=send_async_email,
           args=[app, msg]).start()
    return thr

def send_password_reset_email(user):
    token=user.get_reset_password_token()
    send_email( subject='Reset Your password',
                recipients=[user.email],
                template='auth/reset_password',
                user=user, token=token)
