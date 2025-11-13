from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.models import OTP
from Core.config import settings
import random, smtplib
from email.mime.text import MIMEText
from datetime import datetime
from fastapi_mail import FastMail, MessageSchema
from Core.config import settings
from models.models import OTP
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

#conf = settings.MAIL_CONFIG
async def sendOtp(email: str, db: Session):
    try:
        code = str(random.randint(100000, 999999))
        expires_at = datetime.now() + timedelta(minutes=5)

        otp = OTP(email=email, code=code, expires_at=expires_at)
        db.add(otp)
        db.commit()

        message = MessageSchema(
            subject="Votre code de vérification",
            recipients=[email],
            body=f"Bonjour,\n\nVoici votre code de vérification : {code}\nIl expire dans 5 minutes.",
            subtype="plain",
        )

        fm = FastMail(conf)
        await fm.send_message(message)

        return {"message": "OTP envoyé avec succès"}
    except Exception as e:
        print("Erreur d’envoi OTP :", repr(e))
        return {"detail": "Erreur d’envoi d’e-mail"}


def verify_otp(email: str, code: str, db: Session):
    otp = db.query(OTP).filter(OTP.email == email,OTP.code == code).first()
    
    if not otp:
        return {"success": False, "message": "Code invalide"}

    if datetime.now() > otp.expires_at:
        return {"success": False, "message": "Code expiré"}
    
    db.delete(otp)
    db.commit()
    return {"success": True, "message": "Code correct"}

            
