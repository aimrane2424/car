import sqlite3

def migrate_database():
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    
    # Ajouter la colonne statut si elle n'existe pas
    try:
        c.execute("ALTER TABLE reservations ADD COLUMN statut TEXT DEFAULT 'pending'")
        print("✅ Colonne 'statut' ajoutée à la table reservations")
    except:
        print("ℹ️ Colonne 'statut' existe déjà")
    
    # Mettre à jour les statuts existants
    c.execute("UPDATE reservations SET statut = 'pending' WHERE statut IS NULL")
    
    # Créer un index pour améliorer les performances
    c.execute("CREATE INDEX IF NOT EXISTS idx_reservations_statut ON reservations(statut)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_reservations_email ON reservations(email)")
    
    conn.commit()
    conn.close()
    print("✅ Migration terminée avec succès")

if __name__ == '__main__':
    migrate_database()