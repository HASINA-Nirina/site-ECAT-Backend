# -*- coding: utf-8 -*-
import psycopg2

try:
    conn = psycopg2.connect(
        dbname="site_ecat",     
        user="postgres",        
        password="citron",     
        host="127.0.0.1",       
        port=5432
    )
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("R?sultat:", cur.fetchone())
    cur.close()
    conn.close()
    print("Connexion OK")
except Exception as e:
    print("Erreur :", e)
