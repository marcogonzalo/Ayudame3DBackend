import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

FRONTEND_URL = os.environ.get('FRONTEND_URL')

def __send_email(message):
    mail = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    try:
        response = mail.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
        return True
    except Exception as e:
        print(str(e))
        return False

def new_order_mail(helper, order):
    msg = Mail(
        from_email=os.environ.get('MAIL_DEFAULT_SENDER'),
        to_emails=helper.email,
        subject='Nuevo pedido de Ayúdame3D',
        html_content=('<h1>Tienes un nuevo pedido de Ayúdame3D</h1>'
                    f'<p>Para aceptar o rechazar el nuevo pedido, ingresa aquí: {FRONTEND_URL}/orders/{order.id}'
        )
    )
    return __send_email(msg)

def order_acceptance_mail(order):
    msg = Mail(
        from_email=os.environ.get('MAIL_DEFAULT_SENDER'),
        to_emails=os.environ.get('MAIL_DEFAULT_SENDER'),
        subject=f'El pedido {order.id} ha sido aceptado',
        html_content=('<h1>¡Enhorabuena!</h1>'
                    f'<p>El pedido {order.id} ha sido aceptado.</p>'
        )
    )
    return __send_email(msg)

def order_rejection_mail(order):
    msg = Mail(
        from_email=os.environ.get('MAIL_DEFAULT_SENDER'),
        to_emails=os.environ.get('MAIL_DEFAULT_SENDER'),
        subject=f'ATENCIÓN: El pedido {order.id} ha sido rechazado',
        html_content=('<h1>¡Atención!</h1>'
                    f'<p>El pedido {order.id} ha sido rechazado.</p>'
        )
    )
    return __send_email(msg)

def order_status_update_mail(order):
    status = Status.query.get(order.status_id) 
    msg = Mail(
        from_email=os.environ.get('MAIL_DEFAULT_SENDER'),
        to_emails=os.environ.get('MAIL_DEFAULT_SENDER'),
        subject=f'El pedido {order.id} ha cambiado de estado',
        html_content=(f'<h1>El pedido {order.id} ha cambiado de estado</h1>'
                    f'<p>El pedido {order.id} ha sido cambiado a {status.name}.</p>'
        )
    )
    return __send_email(msg)

def order_new_data_mail(order):
    status = Status.query.get(order.status_id) 
    msg = Mail(
        from_email=os.environ.get('MAIL_DEFAULT_SENDER'),
        to_emails=os.environ.get('MAIL_DEFAULT_SENDER'),
        subject=f'El pedido {order.id} ha cambiado de estado',
        html_content=(f'<h1>El pedido {order.id} ha cambiado de estado</h1>'
                    f'<p>El pedido {order.id} ha sido cambiado a {status.name}.</p>'
        )
    )
    return __send_email(msg)
