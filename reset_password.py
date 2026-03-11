#!/usr/bin/env python3
"""
Script pour réinitialiser le mot de passe admin
"""

import sqlite3
from werkzeug.security import generate_password_hash

def reset_admin_password():
    print("🔄 Réinitialisation du mot de passe admin...")
    
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    
    # Créer la table si elle n'existe pas
    c.execute('''CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Mot de passe par défaut
    username = "admin"
    password = "admin12"
    
    # Générer le hash
    password_hash = generate_password_hash(password)
    
    # Mettre à jour ou insérer
    c.execute('''INSERT OR REPLACE INTO admin_users (username, password_hash) 
                 VALUES (?, ?)''', (username, password_hash))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Mot de passe réinitialisé avec succès!")
    print(f"👤 Username: {username}")
    print(f"🔑 Password: {password}")
    print(f"📝 Hash: {password_hash[:50]}...")
    print("\nVous pouvez maintenant vous connecter avec admin/admin123")

if __name__ == "__main__":
    reset_admin_password()