#!/usr/bin/env python3
"""
ملف لإعادة ضبط قاعدة البيانات بالكامل
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def reset_database():
    print("🔄 إعادة ضبط قاعدة البيانات...")
    print("-" * 50)
    
    # حذف الملف القديم إذا كان موجود
    if os.path.exists('autolocation.db'):
        try:
            os.remove('autolocation.db')
            print("🗑️ قاعدة البيانات القديمة محذوفة")
        except:
            print("⚠️ تعذر حذف قاعدة البيانات القديمة")
    
    # إنشاء اتصال جديد
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    
    # ====== 1. جدول الحجوزات ======
    c.execute('''CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    selectedCar TEXT NOT NULL,
                    dateDebut TEXT NOT NULL,
                    dateFin TEXT NOT NULL,
                    prix_total REAL NOT NULL,
                    statut TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    print("✅ جدول الحجوزات منشأ")
    
    # ====== 2. جدول المستخدمين ======
    c.execute('''CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    print("✅ جدول المستخدمين منشأ")
    
    # ====== 3. جدول المركبات ======
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    price_per_day REAL NOT NULL,
                    description TEXT,
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    print("✅ جدول المركبات منشأ")
    
    # ====== 4. جدول الشات بوت ======
    c.execute('''CREATE TABLE IF NOT EXISTS chatbot_faq (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    print("✅ جدول الشات بوت منشأ")
    
    # ====== 5. إضافة بيانات افتراضية ======
    print("-" * 50)
    print("📥 إضافة البيانات الافتراضية...")
    
    # 5.1 المستخدم الافتراضي
    password_hash = generate_password_hash("admin12")
    try:
        c.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
                  ("admin", password_hash))
        print("✅ المستخدم الافتراضي: admin/admin12")
    except:
        print("⚠️ المستخدم موجود مسبقاً")
    
    # 5.2 المركبات الافتراضية
    default_vehicles = [
        ("Dacia Logan 2025", 350, "Familiale • 5 places • Économique • Climatisation", 
         "https://cdn.motor1.com/images/mgl/9r2nA/s3/dacia-logan-2023.jpg"),
        ("Dacia Sandero Stepway", 300, "Crossover • Robuste • Moderne • GPS optionnel", 
         "https://cdn.motor1.com/images/mgl/mMxRMr/s1/dacia-sandero-stepway-2023.jpg"),
        ("Renault Clio 5", 280, "Citadine • Agile • Confortable • Basse consommation", 
         "https://www.automobile-magazine.fr/asset/cms/175x122/368058/config/265614/renault-clio-5-2023.jpg"),
        ("Peugeot 208", 320, "Design moderne • Écran tactile • Économique", 
         "https://cdn.imagin.studio/getImage?customer=img&make=peugeot&modelFamily=208&modelRange=208&modelVariant=hb&modelYear=2023&powerTrain=fossil&transmission=0&bodySize=5&trim=0&paintId=pspc0003&angle=23"),
        ("Hyundai Tucson", 450, "SUV • Spacieux • Tout-terrain • Sécurité avancée", 
         "https://cdn.imagin.studio/getImage?customer=img&make=hyundai&modelFamily=tucson&modelRange=tucson&modelVariant=hb&modelYear=2023&powerTrain=fossil&transmission=0&bodySize=5&trim=0&paintId=pspc0003&angle=23")
    ]
    
    for vehicle in default_vehicles:
        try:
            c.execute("INSERT INTO vehicles (model, price_per_day, description, image_url) VALUES (?, ?, ?, ?)",
                      vehicle)
        except:
            pass
    
    print(f"✅ {len(default_vehicles)} مركبات افتراضية")
    
    # 5.3 أسئلة الشات بوت الافتراضية
    default_faq = [
        ("bonjour", "👋 Bonjour ! Je suis l'assistant AutoLocation. Comment puis-je vous aider aujourd'hui ?", "salutation"),
        ("prix", "💰 Nos prix varient entre 280 et 500 DH/jour. Détails complets sur la page Réservation.", "prix"),
        ("réservation", "📋 Pour réserver: 1) Choisissez véhicule 2) Remplissez formulaire 3) Confirmez. Ou appelez 06 00 00 00 00.", "réservation"),
        ("documents", "📄 Documents requis: Carte d'identité + permis valide + carte bancaire pour caution.", "documents"),
        ("assurance", "🛡️ Assurance RC incluse. Tous risques: +80 DH/jour. Franchise: 2000 DH.", "assurance"),
        ("livraison", "🚚 Livraison gratuite à Casablanca pour 5+ jours. Autres villes: nous consulter.", "services"),
        ("annulation", "🔄 Annulation gratuite jusqu'à 48h avant. Moins de 48h: 1 jour facturé.", "conditions"),
        ("caution", "💳 Caution: 2000-5000 DH selon véhicule. Remboursée sous 7 jours.", "paiement"),
        ("kilométrage", "📏 250 km/jour inclus. Supplément: 2 DH/km. Option illimitée: +50 DH/jour.", "conditions"),
        ("essence", "⛽ Véhicule rendu avec plein. Si non: plein facturé + 50 DH service.", "conditions")
    ]
    
    for faq in default_faq:
        try:
            c.execute("INSERT INTO chatbot_faq (question, answer, category) VALUES (?, ?, ?)", faq)
        except:
            pass
    
    print(f"✅ {len(default_faq)} سؤال افتراضي للشات بوت")
    
    # 5.4 حجوزات تجريبية
    demo_reservations = [
        ("Ahmed Benali", "ahmed@email.com", "0601111111", "Dacia Logan 2025", "2025-02-01", "2025-02-05", 1400),
        ("Fatima Zahra", "fatima@email.com", "0602222222", "Renault Clio 5", "2025-02-10", "2025-02-12", 560),
        ("Karim Alami", "karim@email.com", "0603333333", "Peugeot 208", "2025-02-15", "2025-02-20", 1600),
    ]
    
    for res in demo_reservations:
        try:
            c.execute("INSERT INTO reservations (nom, email, phone, selectedCar, dateDebut, dateFin, prix_total) VALUES (?, ?, ?, ?, ?, ?, ?)", res)
        except:
            pass
    
    print(f"✅ {len(demo_reservations)} حجوزات تجريبية")
    
    # حفظ التغييرات وإغلاق الاتصال
    conn.commit()
    conn.close()
    
    print("-" * 50)
    print("🎉 قاعدة البيانات جاهزة!")
    print("\n🔑 بيانات الدخول:")
    print("   👤 المستخدم: admin")
    print("   🔑 كلمة المرور: admin12")
    print("\n🌐 روابط الموقع:")
    print("   • الموقع: http://localhost:5000")
    print("   • تسجيل الدخول: http://localhost:5000/admin_login.html")
    print("   • لوحة التحكم: http://localhost:5000/admin_dashboard.html")
    print("-" * 50)

if __name__ == "__main__":
    reset_database()