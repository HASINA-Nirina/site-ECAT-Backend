from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.models import OTP
from Core.config import Settings
import random, smtplib
from email.mime.text import MIMEText
from datetime import datetime

def generate_otp():
    return str(random.randint(100000, 999999))

def send_email(receiver, subject, message):
    try:
        with smtplib.SMTP(Settings.SMTP_SERVER, Settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(Settings.EMAIL_SENDER, Settings.EMAIL_PASSWORD)
            msg = MIMEText(message)
            msg["Subject"] = subject
            msg["From"] = Settings.EMAIL_SENDER
            msg["To"] = receiver
            server.sendmail(Settings.EMAIL_SENDER, receiver, msg.as_string())

    except smtplib.SMTPAuthenticationError as e:
            print("Erreur d'authentification SMTP:", e.smtp_code, e.smtp_error)
            raise HTTPException(status_code=500, detail="Erreur d’authentification SMTP")
    except Exception as e:
         print("Erreur SMTP:", e)
         raise HTTPException(status_code=500, detail="Erreur d’envoi d’e-mail")

def  sendOtp(email: str, db: Session):
    code = generate_otp()
    otp = OTP(email=email, code=code)
    db.add(otp)
    db.commit()
    send_email(email, "Votre code OTP", f"Votre code est {code} (valide 5 min)")
    return {"message": "OTP envoyé avec succès."}

def verify_otp(email: str, code: str, db: Session):
    otp = db.query(OTP).filter(OTP.email == email, OTP.code == code).first()
    
    if not otp:
        return {"success": False, "message": "Code invalide"}

    if datetime.now() > otp.expires_at:
        return {"success": False, "message": "Code expiré"}
    
    db.delete(otp)
    db.commit()
    return {"success": True, "message": "Code correct"}

            
