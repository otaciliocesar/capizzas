from mailersend import emails

mailer = emails.NewEmail()

def enviar_email(destinatarios, assunto, texto, html=None):
    if isinstance(destinatarios, str):
        destinatarios = [destinatarios]

    mail_body = {
        "from": {
            "email": "contatocapizzas@gmail.com",  # E-mail verificado no MailerSend
            "name": "Capizzas"
        },
        "to": [{"email": email} for email in destinatarios],
        "subject": assunto,
        "text": texto,
        "html": html or texto
    }

    response = mailer.send(mail_body)
    return response
