#19-02-2026
import smtplib
from email.message import EmailMessage
def send_mail(to,body,subject):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('babjiasha1@gmail.com','zovq opsu gnhf xedh')  #app password
    msg=EmailMessage()
    msg['FROM']='babjiasha1@gmail.com'
    msg['TO']=to
    msg['SUBJECT']=subject
    msg.set_content(body)
    server.send_message(msg)
    server.close()

