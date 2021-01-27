import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from models import Status

FRONTEND_URL = os.environ.get('FRONTEND_URL')

def __send_email(message):
    try:
        mail = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = mail.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
        return True
    except Exception as e:
        print(str(e))
        return False

def __get_template_message(message):
    header = '<div style="background-color: #40519f; color: #ffffff; padding: 40px 10px; text-align: center; width: 100%;">Ayúdame 3D</div>'
    content = f'<div>{message}</div>'
    footer = '<div style="background-color: #40519f; color: #ffffff; padding: 40px 10px; text-align: center; width: 100%;">Ayúdame 3D</div>'
    return header + content + footer

def new_order_mail(helper, order):
    url = f'{FRONTEND_URL}/orders/{order.id}'
    msg = Mail(
        from_email=os.environ.get('MAIL_DEFAULT_SENDER'),
        to_emails=helper.email,
        subject='Nueva solicitud de Ayúdame3D',
        html_content=(
            __get_template_message(
                '<h1>¡Hola! Tienes una nueva solicitud de Ayúdame3D</h1>'
                f'<p>Acabas de recibir una nueva solicitud de Ayúdame3D en tu cuenta de Helper. Para ver todos los detalles entra aquí: <a href="{url}">{url}</a></p>'
                '¡Gracias!'
            )
        )
    )
    return __send_email(msg)

def order_acceptance_mail(order):
    msg = Mail(
        from_email=os.environ.get('MAIL_DEFAULT_SENDER'),
        to_emails=os.environ.get('MAIL_DEFAULT_SENDER'),
        subject=f'La solicitud {order.id} ha sido aceptada',
        html_content=(
            __get_template_message(
                '<h1>¡Enhorabuena!</h1>'
                f'<p>El pedido {order.id} ha sido aceptado.</p>'
            )
        )
    )
    return __send_email(msg)

def order_rejection_mail(order):
    msg = Mail(
        from_email=os.environ.get('MAIL_DEFAULT_SENDER'),
        to_emails=os.environ.get('MAIL_DEFAULT_SENDER'),
        subject=f'ATENCIÓN: El pedido {order.id} ha sido rechazado',
        html_content=(
            __get_template_message(
                '<h1>¡Atención!</h1>'
                f'<p>El pedido {order.id} ha sido rechazado.</p>'
            )
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
        html_content=(
            __get_template_message(
                f'<h1>El pedido {order.id} ha cambiado de estado</h1>'
                f'<p>El pedido {order.id} ha sido cambiado a {status.name}.</p>'
            )
        )
    )
    return __send_email(msg)

def order_complete_mail(order):
    video_url = 'https://youtu.be/fGFLQlRpeQI'
    form_url = 'https://docs.google.com/forms/d/e/1FAIpQLSfaUth4_hhjTopk594-ia6RVkkq2Fq9mcRRhAq8ggW0SbBMgA/viewform?usp=sf_link'
    status = Status.query.get(order.status_id) 
    msg = Mail(
        from_email=os.environ.get('MAIL_DEFAULT_SENDER'),
        to_emails=helper.email,
        subject=f'Ayúdame 3D ha aceptado tu video en el pedido {order.id}',
        html_content=(
            __get_template_message(
                '<h1>¡Todo correcto!</h1>'
                f'<p>Buenas, ¡muchas gracias por toda tu información adjunta! Hemos comprobado que está todo correcto por lo que procedemos a la preparación del paquete.</p>'
                f'<p>En el siguiente vídeo encontrarás <b>cómo preparar el envío</b>: <a href="{video_url}">{video_url}</a></p>'
                f'<p>Finalmente, por favor, <b>el siguiente formulario para definir día y hora de recogida en la dirección que mejor te venga</b>: <a href="{form_url}">{form_url}</a></p>'
            )
        )
    )
    return __send_email(msg)
