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

conf = settings.MAIL_CONFIG


async def sendOtp(email: str, db: Session):
    try:
        # 1. Génération et Sauvegarde
        code = str(random.randint(100000, 999999))
        expires_at = datetime.now() + timedelta(minutes=5)

        otp = OTP(email=email, code=code, expires_at=expires_at)
        db.add(otp)
        db.commit()

        # ✅ HTML stylé (design type Snapchat)
        html_content = f"""
        <div style="font-family: Arial, sans-serif; background-color: #f6f6f6; padding: 20px;">
          <div style="max-width: 480px; margin: auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); overflow: hidden;">
            
            <!-- Bandeau avec logo -->
            <div style="background-color: #f9f9f9; padding: 20px; text-align: center;">
              <img src="https://raw.githubusercontent.com/HASINA-Nirina/site-ECAT-Frontend/main/src/app/assets/logo.jpeg" alt="Logo Université ECAT" style="width: 80px; height: 80px; border-radius: 50%;">
            </div>

            <!-- Titre principal -->
            <div style="padding: 20px; text-align: center; border-top: 5px solid #1177ff;">
              <h2 style="color: #111; margin-bottom: 8px;">Authentification</h2>
              <p style="color: #444; font-size: 14px;">Voici le code de vérification que vous avez demandé pour confirmer votre identité :</p>

              <!-- Code OTP -->
              <div style="margin: 20px auto; font-size: 28px; font-weight: bold; color: #1177ff; letter-spacing: 4px; background-color: #f0f7ff; display: inline-block; padding: 10px 20px; border-radius: 8px;">
                {code}
              </div>

              <p style="font-size: 13px; color: #555; margin-top: 16px;">
                Ce code expirera dans <strong>5 minutes</strong>. Ne le partagez avec personne pour des raisons de sécurité.
              </p>

              <p style="font-size: 13px; color: #777; margin-top: 10px;">
                Si vous n’êtes pas à l’origine de cette demande, ignorez simplement cet e-mail.
              </p>
            </div>

            <!-- Pied de page coloré -->
            <div style="background-color: #1177ff; height: 10px;"></div>
          </div>

          <!-- Signature -->
          <p style="text-align: center; font-size: 12px; color: #666; margin-top: 16px;">
            © 2025 Université ECAT Taratra Fianarantsoa
          </p>
        </div>
        """

        # 3. Configuration du message
        message = MessageSchema(
            subject="Votre code de vérification ECAT",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html # Utilisez l'énumération MessageType pour plus de sécurité
        )

        # 4. Envoi via FastMail en utilisant vos paramètres centralisés
        fm = FastMail(settings.MAIL_CONFIG)
        await fm.send_message(message)

        print(f"✅ OTP envoyé avec succès à {email}")
        return True # On retourne un booléen simple pour la logique interne

    except Exception as e:
        db.rollback() # Annule l'insertion de l'OTP en base si le mail échoue
        print(f"❌ ERREUR CRITIQUE SMTP : {repr(e)}")
        # On lève une VRAIE erreur HTTP pour que le frontend passe dans le bloc catch
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur serveur d'envoi d'e-mail : {str(e)}"
        )
def verify_otp(email: str, code: str, db: Session):
    otp = db.query(OTP).filter(OTP.email == email, OTP.code == code).first()
    
    if not otp:
        return {"success": False, "message": "Code invalide"}

    if datetime.now() > otp.expires_at:
        return {"success": False, "message": "Code expiré"}
    
    db.delete(otp)
    db.commit()
    return {"success": True, "message": "Code correct"}
