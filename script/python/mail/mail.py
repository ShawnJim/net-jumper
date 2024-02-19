import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys


def send_email(sender_email, sender_name, password, receiver_email, subject,  message_body):
    # 创建一个多部分的消息
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{sender_name} <{sender_email}>"
    message["To"] = receiver_email

    # 创建邮件正文
    text = message_body
    html = f"""\
    <html>
      <body>
        <p>{message_body}</p>
      </body>
    </html>
    """

    # 将文本和HTML版本的正文转换为MIMEText对象并添加到MIMEMultipart消息中
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)

    # 连接到SMTP服务器
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

    print("邮件已发送！")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python send_email.py sender_email sender_name password receiver_email subject message_body")
        sys.exit(1)

    sender_email = sys.argv[1]
    sender_name = sys.argv[2]
    password = sys.argv[3]
    receiver_email = sys.argv[4]
    subject = sys.argv[5]
    message_body = sys.argv[6]

    send_email(sender_email, sender_name, password, receiver_email, subject, message_body)
