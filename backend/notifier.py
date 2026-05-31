import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import asyncio
import os

class EmailNotifier:
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587, sender_email=None, password=None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.password = password
        self.receiver_email = "YOUR EMAIL"

    async def send_alert(self, subject, message, image_path=None):
        if not self.sender_email or not self.password:
            print(f"Email alert suppressed (no credentials): {subject}")
            return

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.receiver_email
        msg['Subject'] = f"[Sentinel AI Alert] {subject}"

        msg.attach(MIMEText(message, 'plain'))

        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
                msg.attach(img)

        try:
            # Use asyncio to run in thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_sync, msg)
            print(f"Email alert sent to {self.receiver_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def _send_sync(self, msg):
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.password)
            server.send_message(msg)
