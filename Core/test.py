import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# 👉 Mets ici ta chaîne de connexion originale :
DATABASE_URL = "postgresql://postgres:gelie@localhost:5432/site-ecat"

print("=== Vérification de la chaîne de connexion ===")
print("Chaîne originale :", DATABASE_URL)

# --- Vérifie s’il y a des caractères non ASCII ---
if any(ord(c) > 127 for c in DATABASE_URL):
    print("⚠️ Caractère non-ASCII détecté (accent, espace, etc.)")
else:
    print("✅ Aucun caractère spécial détecté dans l'URL.")

# --- Encode automatiquement la partie mot de passe si besoin ---
try:
    userpass_part = DATABASE_URL.split("@")[0].split("//")[1]
    if ":" in userpass_part:
        user, password = userpass_part.split(":", 1)
        encoded_password = urllib.parse.quote(password)
        encoded_url = DATABASE_URL.replace(password, encoded_password)
        print("\n🔒 Chaîne encodée :", encoded_url)
        DATABASE_URL = encoded_url
except Exception as e:
    print("Erreur pendant l'encodage :", e)

# --- Test de connexion ---
print("\n=== Test de connexion à PostgreSQL ===")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute("SELECT version();")
        print("✅ Connexion réussie à :", result.scalar())
except SQLAlchemyError as e:
    print("❌ Erreur de connexion :", e)
