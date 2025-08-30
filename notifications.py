import os
from mailersend import MailerSendClient, EmailBuilder
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MAILERSEND_API_KEY = os.environ.get("MAILERSEND_API_KEY")
MONGODB_URI = os.environ.get("MONGODB_URI")

client = MongoClient(MONGODB_URI)
db = client["tfg_db"]
users = db["users"]
articles = db["articles"]

ms = MailerSendClient()

def send_notifications():
  for user in users.find():
    email = user.get("email")
    subscribed_categories = user.get("subscribed_categories", [])

    if subscribed_categories:
      matching_articles = list(articles.find({"category": {"$in": subscribed_categories}, "language": "es"}))
      if matching_articles:
        mail_body = {}
        mail_from = {"email": "GenNews@test-nrw7gymdnzrg2k8e.mlsender.net", "name": "GenNews"}
        recipients = [{"email": email, "name": user.get("username")}]
        article_list = "\n".join([f"- {article['title']}" for article in matching_articles])
        subject = "Nuevos artículos en tus categorías suscritas"

        body = f"Hola {user.get('username')},\nAquí tienes los nuevos artículos en tus categorías suscritas:\n\n"
        for article in matching_articles:
            body += f"- {article['title']}: https://gennews.vercel.app/articles/{article['_id']}\n"
        body += "\nSaludos,\nGenNews."

        html = f"<p>Hola {user.get('username')},</p><p>Aquí tienes los nuevos artículos en tus categorías suscritas:</p><ul>"
        for article in matching_articles:
            html += f"<li><a href='https://gennews.vercel.app/{article['_id']}'>{article['title']}</a></li>"
        html += "</ul><p>Saludos,<br>GenNews.</p>"

        notification_email = (EmailBuilder()
         .from_email("GenNews@test-nrw7gymdnzrg2k8e.mlsender.net", "GenNews")
         .to_many(recipients)
         .subject(subject)
         .html(html)
         .text(body)
         .build())
        try:
          response = ms.emails.send(notification_email)
        except Exception as e:
          print(f"Error al enviar el correo a {email}: {e}")