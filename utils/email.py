from django.core.mail import EmailMultiAlternatives

def enviar_email(destinatario, assunto, corpo_texto, corpo_html):
    msg = EmailMultiAlternatives(
        assunto,
        corpo_texto,
        'contato@capizzas.com',
        [destinatario]
    )
    msg.attach_alternative(corpo_html, "text/html")
    msg.send()