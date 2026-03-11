# main.py - النسخة النهائية الكاملة (2026)

from flask import Flask, request, send_from_directory, jsonify, session
from flask_cors import CORS
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import SnowballStemmer
import nltk
import string
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# تحميل NLTK
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

app = Flask(__name__, static_folder='.')
CORS(app, supports_credentials=True)

# إعدادات
app.secret_key = 'auto_location_secret_key_2026_important'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=3)

# ====== الشات بوت الذكي ======
stemmer = SnowballStemmer('french')
stopwords_fr = set(nltk.corpus.stopwords.words('french'))
vectorizer = TfidfVectorizer()
questions = []
answers = []

def preprocess(text):
    """معالجة النص للشات بوت"""
    text = text.lower()
    text = ''.join([c for c in text if c not in string.punctuation])
    tokens = nltk.word_tokenize(text, language='french')
    tokens = [stemmer.stem(t) for t in tokens if t not in stopwords_fr]
    return ' '.join(tokens)

def load_chatbot_data():
    """تحميل بيانات الشات بوت من جميع المصادر"""
    global questions, answers, vectorizer
    try:
        dfs = []
        
        # 1. تحميل من voitures.csv
        try:
            df_csv = pd.read_csv('voitures.csv', encoding='utf-8')
            df_csv = df_csv.rename(columns={'reponse': 'answer'})
            df_csv = df_csv[['question', 'answer']]
            dfs.append(df_csv)
            print(f"✅ voitures.csv محمل: {len(df_csv)} سؤال")
        except Exception as e:
            print(f"⚠️ مشكل فvoitures.csv: {e}")
        
        # 2. تحميل من services_info.csv
        try:
            df_services = pd.read_csv('services_info.csv', encoding='utf-8')
            df_services = df_services.rename(columns={'reponse': 'answer'})
            df_services = df_services[['question', 'answer']]
            dfs.append(df_services)
            print(f"✅ services_info.csv محمل: {len(df_services)} سؤال")
        except Exception as e:
            print(f"⚠️ مشكل فservices_info.csv: {e}")
        
        # 3. تحميل من قاعدة البيانات
        try:
            conn = sqlite3.connect('autolocation.db')
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chatbot_faq'")
            if c.fetchone():
                df_db = pd.read_sql_query("SELECT question, answer FROM chatbot_faq", conn)
                if not df_db.empty:
                    dfs.append(df_db)
                    print(f"✅ قاعدة بيانات محمل: {len(df_db)} سؤال")
            conn.close()
        except Exception as e:
            print(f"⚠️ مشكل فقاعدة البيانات: {e}")
        
        # جمع كل البيانات
        if dfs:
            df_all = pd.concat(dfs, ignore_index=True)
            df_all = df_all.dropna(subset=['question', 'answer'])
            questions = df_all['question'].str.lower().tolist()
            answers = df_all['answer'].tolist()
            
            # معالجة النصوص
            processed = [preprocess(q) for q in questions]
            vectorizer = TfidfVectorizer()
            vectorizer.fit(processed)
            
            print(f"🤖 الشات بوت محمل: {len(questions)} سؤال/جواب")
        else:
            # نسخة احتياطية
            questions = ["bonjour", "prix", "réservation", "documents"]
            answers = [
                "👋 Bonjour ! Je suis l'assistant AutoLocation. Comment puis-je vous aider ?",
                "💰 Nos prix: 250-500 DH/jour selon modèle. Détails sur la page Réservation.",
                "📋 Réservez en ligne ou par téléphone au 06 00 00 00 00.",
                "📄 Carte d'identité + permis valide requis. Âge minimum: 21 ans."
            ]
            processed = [preprocess(q) for q in questions]
            vectorizer.fit(processed)
            
    except Exception as e:
        print(f"❌ خطأ فتحميل الشات بوت: {e}")

# ====== تهيئة قاعدة البيانات ======
def init_db():
    """تهيئة قاعدة البيانات"""
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    
    # جدول الحجوزات
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
    
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )''')
    
    # جدول المركبات
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    price_per_day REAL NOT NULL,
                    description TEXT,
                    image_url TEXT
                )''')
    
    # جدول FAQ للشات بوت
    c.execute('''CREATE TABLE IF NOT EXISTS chatbot_faq (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # إضافة مستخدم افتراضي إذا لم يكن موجود
    c.execute("SELECT COUNT(*) FROM admin_users")
    if c.fetchone()[0] == 0:
        password_hash = generate_password_hash("admin12")
        c.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
                  ("admin", password_hash))
        print("✅ المستخدم الافتراضي مضاف: admin/admin12")
    
    # إضافة مركبات افتراضية
    c.execute("SELECT COUNT(*) FROM vehicles")
    if c.fetchone()[0] == 0:
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
        c.executemany("INSERT INTO vehicles (model, price_per_day, description, image_url) VALUES (?, ?, ?, ?)", 
                      default_vehicles)
        print(f"✅ {len(default_vehicles)} مركبات افتراضية مضافين")
    
    # إضافة FAQ افتراضية
    c.execute("SELECT COUNT(*) FROM chatbot_faq")
    if c.fetchone()[0] == 0:
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
        c.executemany("INSERT INTO chatbot_faq (question, answer, category) VALUES (?, ?, ?)", default_faq)
        print(f"✅ {len(default_faq)} FAQ افتراضية مضافين")
    
    conn.commit()
    conn.close()

# ====== مصادقة المسؤول ======
def admin_required(f):
    """مصادقة للمسؤول"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({"success": False, "error": "Accès refusé. Connectez-vous en tant qu'admin."}), 401
        return f(*args, **kwargs)
    return wrapper

# ====== الرواتب الرئيسية ======
@app.route('/')
@app.route('/<path:path>')
def serve(path='index.html'):
    """تقديم الملفات الثابتة"""
    return send_from_directory('.', path)

# ====== API للحجوزات ======
@app.route('/api/reserve', methods=['POST'])
def reserve():
    """حجز جديد"""
    data = request.form
    try:
        conn = sqlite3.connect('autolocation.db')
        c = conn.cursor()
        c.execute("""INSERT INTO reservations 
                     (nom, email, phone, selectedCar, dateDebut, dateFin, prix_total)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (data['nom'], data['email'], data['phone'], data['selectedCar'],
                   data['dateDebut'], data['dateFin'], float(data['prix_total'])))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "✅ Réservation enregistrée avec succès !"})
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur: {str(e)}"}), 500

# ====== API للمركبات ======
@app.route('/api/vehicles')
def api_vehicles():
    """الحصول على جميع المركبات"""
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("SELECT model, price_per_day AS price, description, image_url AS image FROM vehicles ORDER BY price")
    rows = c.fetchall()
    vehicles = [dict(zip(['model', 'price', 'description', 'image'], row)) for row in rows]
    conn.close()
    return jsonify({"success": True, "vehicles": vehicles})

# ====== API للشات بوت ======
@app.route('/api/chat', methods=['POST'])
def chat():
    """رد الشات بوت"""
    message = request.form.get('message', '').strip()
    if not message:
        return jsonify({"success": False, "error": "Message vide"}), 400
    
    lower_msg = message.lower()
    
    # الاتصال بقاعدة البيانات
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    
    # 1. تحيات بسيطة
    if any(word in lower_msg for word in ["bonjour", "salut", "hello", "hi", "coucou", "bonsoir"]):
        conn.close()
        return jsonify({
            "success": True, 
            "response": "👋 Bonjour ! Je suis l'assistant AutoLocation. Je peux vous aider avec:\n\n• 📋 Réservations\n• 🚗 Modèles et prix\n• 📞 Contact\n• 📄 Conditions\n• 🛡️ Assurance"
        })
    
    if "merci" in lower_msg:
        conn.close()
        return jsonify({"success": True, "response": "Je vous en prie ! 😊 N'hésitez pas si vous avez d'autres questions."})
    
    if any(word in lower_msg for word in ["au revoir", "bye", "à plus", "à bientôt"]):
        conn.close()
        return jsonify({"success": True, "response": "À bientôt ! Bonne route 🚗"})
    
    # 2. البحث عن مركبات محددة
    c.execute("SELECT model, price_per_day, description FROM vehicles")
    db_vehicles = c.fetchall()
    
    for model, price, desc in db_vehicles:
        model_lower = model.lower()
        if (model_lower in lower_msg or 
            any(word in lower_msg for word in model_lower.split())):
            conn.close()
            return jsonify({
                "success": True,
                "response": f"🚗  {model}\n\n💰 Prix: {price} DH/jour\n📝 Description: {desc}\n\n📋 Disponible maintenant  sur la page Réservation!"
            })
    
    # 3. البحث بالكلمات المفتاحية
    # أسعار
    if any(word in lower_msg for word in ["prix", "tarif", "combien", "cout", "coût", "dh", "euro", "price"]):
        c.execute("SELECT model, price_per_day FROM vehicles ORDER BY price_per_day")
        prices = c.fetchall()
        
        if prices:
            price_list = "\n".join([f"• {model}: {price} DH/jour" for model, price in prices])
            min_price = min([p[1] for p in prices])
            max_price = max([p[1] for p in prices])
            
            conn.close()
            return jsonify({
                "success": True,
                "response": f"💰 Nos tarifs actuels :\n\n{price_list}\n\n📊  Fourchette**: {min_price} - {max_price} DH/jour\n\n🎁 Remises :\n- 7+ jours: -15%\n- 1+ mois: -20%\n- Étudiants: -10%"
            })
    
    # حجز
    if any(word in lower_msg for word in ["reserver", "réservation", "louer", "location", "prendre", "disponible", "disponibilité"]):
        c.execute("SELECT COUNT(*) FROM vehicles")
        count = c.fetchone()[0]
        
        conn.close()
        return jsonify({
            "success": True,
            "response": f"📋 Réservation en ligne \n\n✅ {count} véhicules disponibles\n📞 Tél : 06 00 00 00 00\n🌐 Site : Page 'Réservation'\n📱 App mobile : Disponible\n\n📝 Étapes**:\n1. Choisir véhicule\n2. Sélectionner dates\n3. Remplir formulaire\n4. Confirmer"
        })
    
    # مستندات
    if any(word in lower_msg for word in ["condition", "document", "permis", "age", "âge", "carte", "identité"]):
        conn.close()
        return jsonify({
            "success": True,
            "response": "📄 Conditions générales :\n\n• Âge minimum: 21 ans\n• Permis valide depuis 2 ans\n• Carte d'identité obligatoire\n• Caution: 2000-5000 DH\n• Assurance incluse\n• Pas de fumée dans véhicules\n• Kilométrage: 250 km/jour inclus"
        })
    
    # اتصل بنا
    if any(word in lower_msg for word in ["contact", "téléphone", "tel", "adresse", "agence", "localisation", "où", "ou"]):
        conn.close()
        return jsonify({
            "success": True,
            "response": "📍 Nous contacter:\n\n📞 Téléphone : 06 00 00 00 00\n📧 Email: contact@autolocation.ma\n🏢 Agences : Casablanca, Rabat, Marrakech\n🕐 Horaires : 8h-20h (lun-sam)\n\n🗺️  Carte: Voir page 'Localisation'"
        })
    
    conn.close()
    
    # 4. البحث في أسئلة الشات بوت
    if questions:
        processed_msg = preprocess(message)
        if processed_msg:
            try:
                msg_vec = vectorizer.transform([processed_msg])
                quest_vec = vectorizer.transform([preprocess(q) for q in questions])
                similarities = cosine_similarity(msg_vec, quest_vec)[0]
                max_sim_idx = similarities.argmax()
                
                if similarities[max_sim_idx] > 0.3:  # عتبة التشابه
                    return jsonify({
                        "success": True,
                        "response": answers[max_sim_idx]
                    })
            except:
                pass
    
    # 5. رد افتراضي
    return jsonify({
        "success": True,
        "response": "🤖 AutoLocation Assistant\n\nJe ne suis pas sûr d'avoir compris. Je peux vous aider avec:\n\n🚗 Véhicules: Modèles, prix, disponibilités\n📋 Réservation: Comment réserver, conditions\n📞 **Contact**: Agences, téléphone, email\n🛡️ **Services**: Assurance, options, livraison\n\n📞 **Pour une réponse précise**: 06 00 00 00 00"
    })

# ====== إدارة المسؤول ======
@app.route('/admin/login', methods=['POST'])
def admin_login():
    """تسجيل دخول المسؤول"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("SELECT password_hash FROM admin_users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row and check_password_hash(row[0], password):
        session['admin_logged_in'] = True
        session.permanent = True
        return jsonify({"success": True, "message": "Connexion réussie"})
    
    return jsonify({"success": False, "error": "Nom d'utilisateur ou mot de passe incorrect"}), 401

@app.route('/admin/logout')
def admin_logout():
    """تسجيل خروج المسؤول"""
    session.pop('admin_logged_in', None)
    return jsonify({"success": True, "message": "Déconnecté"})

@app.route('/admin/check')
def check_admin():
    """التحقق من حالة المسؤول"""
    if session.get('admin_logged_in'):
        return jsonify({"success": True, "admin": True})
    return jsonify({"success": True, "admin": False})

# ====== إدارة الحجوزات ======
@app.route('/admin/reservations')
@admin_required
def get_reservations():
    """الحصول على جميع الحجوزات"""
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute('''SELECT id, nom, email, phone, selectedCar, dateDebut, dateFin, prix_total, statut 
                 FROM reservations ORDER BY id DESC''')
    rows = c.fetchall()
    reservations = []
    for r in rows:
        reservations.append({
            "id": r[0], "nom": r[1], "email": r[2], "phone": r[3],
            "selectedCar": r[4], "dateDebut": r[5], "dateFin": r[6],
            "prix_total": r[7], "statut": r[8] or "pending"
        })
    conn.close()
    return jsonify({"success": True, "reservations": reservations})

@app.route('/admin/reservations/<int:id>/status', methods=['PUT'])
@admin_required
def update_reservation_status(id):
    """تحديث حالة الحجز"""
    data = request.get_json()
    statut = data.get('status', '').strip()
    
    if statut not in ['pending', 'confirmed', 'cancelled', 'completed']:
        return jsonify({"success": False, "error": "Statut invalide"}), 400
    
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("UPDATE reservations SET statut = ? WHERE id = ?", (statut, id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Statut mis à jour: {statut}"})

# ====== إدارة المركبات ======
@app.route('/admin/vehicles', methods=['GET'])
@admin_required
def get_vehicles():
    """الحصول على جميع المركبات"""
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("SELECT id, model, price_per_day, description, image_url FROM vehicles ORDER BY id")
    rows = c.fetchall()
    vehicles = [{"id": r[0], "model": r[1], "price": r[2], "description": r[3], "image": r[4]} for r in rows]
    conn.close()
    return jsonify({"success": True, "vehicles": vehicles})

@app.route('/admin/vehicles', methods=['POST'])
@admin_required
def add_vehicle():
    """إضافة مركبة جديدة"""
    data = request.json
    model = data.get('model', '').strip()
    price = data.get('price', 0)
    
    if not model or price <= 0:
        return jsonify({"success": False, "error": "Modèle et prix requis"}), 400
    
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("""INSERT INTO vehicles (model, price_per_day, description, image_url)
                 VALUES (?, ?, ?, ?)""",
              (model, price, data.get('description', ''), data.get('image', '')))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Véhicule ajouté"})

@app.route('/admin/vehicles/<int:id>', methods=['PUT'])
@admin_required
def update_vehicle(id):
    """تحديث مركبة"""
    data = request.json
    model = data.get('model', '').strip()
    price = data.get('price', 0)
    
    if not model or price <= 0:
        return jsonify({"success": False, "error": "Modèle et prix requis"}), 400
    
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("""UPDATE vehicles SET model=?, price_per_day=?, description=?, image_url=?
                 WHERE id=?""",
              (model, price, data.get('description', ''), data.get('image', ''), id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Véhicule modifié"})

@app.route('/admin/vehicles/<int:id>', methods=['DELETE'])
@admin_required
def delete_vehicle(id):
    """حذف مركبة"""
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("DELETE FROM vehicles WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Véhicule supprimé"})

# ====== إدارة الشات بوت ======
@app.route('/admin/chatbot', methods=['GET'])
@admin_required
def get_chatbot_qa():
    """الحصول على أسئلة الشات بوت"""
    try:
        conn = sqlite3.connect('autolocation.db')
        c = conn.cursor()
        c.execute("SELECT question, answer FROM chatbot_faq")
        rows = c.fetchall()
        qa_list = [{"question": r[0], "reponse": r[1]} for r in rows]
        conn.close()
        
        return jsonify({"success": True, "qa": qa_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/chatbot', methods=['POST'])
@admin_required
def update_chatbot_qa():
    """تحديث أسئلة الشات بوت"""
    data = request.json.get('qa', [])
    if not data:
        return jsonify({"success": False, "error": "Données vides"}), 400
    
    try:
        conn = sqlite3.connect('autolocation.db')
        c = conn.cursor()
        
        # مسح القديم
        c.execute("DELETE FROM chatbot_faq")
        
        # إضافة الجديد
        for item in data:
            question = item.get('question', '').strip()
            answer = item.get('reponse', '').strip()
            if question and answer:
                c.execute("INSERT INTO chatbot_faq (question, answer) VALUES (?, ?)", 
                          (question, answer))
        
        conn.commit()
        conn.close()
        
        # إعادة تحميل الشات بوت
        load_chatbot_data()
        
        return jsonify({"success": True, "message": "Chatbot mis à jour !"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chatbot/reload', methods=['POST'])
@admin_required
def reload_chatbot():
    """إعادة تحميل الشات بوت"""
    try:
        load_chatbot_data()
        return jsonify({"success": True, "message": "Chatbot rechargé"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/chatbot/faq', methods=['GET'])
@admin_required
def get_chatbot_faq():
    """الحصول على FAQ"""
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("SELECT id, question, answer, category FROM chatbot_faq ORDER BY category")
    rows = c.fetchall()
    faq_items = [{"id": r[0], "question": r[1], "answer": r[2], "category": r[3]} for r in rows]
    conn.close()
    return jsonify({"success": True, "faq": faq_items})

@app.route('/admin/chatbot/faq', methods=['POST'])
@admin_required
def add_chatbot_faq():
    """إضافة FAQ جديدة"""
    data = request.json
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    category = data.get('category', 'general')
    
    if not question or not answer:
        return jsonify({"success": False, "error": "Question et réponse requises"}), 400
    
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("INSERT INTO chatbot_faq (question, answer, category) VALUES (?, ?, ?)",
              (question, answer, category))
    conn.commit()
    conn.close()
    
    load_chatbot_data()
    return jsonify({"success": True, "message": "FAQ ajoutée"})

@app.route('/admin/chatbot/faq/<int:id>', methods=['PUT'])
@admin_required
def update_chatbot_faq(id):
    """تحديث FAQ"""
    data = request.json
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    category = data.get('category', 'general')
    
    if not question or not answer:
        return jsonify({"success": False, "error": "Question et réponse requises"}), 400
    
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("UPDATE chatbot_faq SET question=?, answer=?, category=? WHERE id=?",
              (question, answer, category, id))
    conn.commit()
    conn.close()
    
    load_chatbot_data()
    return jsonify({"success": True, "message": "FAQ mise à jour"})

@app.route('/admin/chatbot/faq/<int:id>', methods=['DELETE'])
@admin_required
def delete_chatbot_faq(id):
    """حذف FAQ"""
    conn = sqlite3.connect('autolocation.db')
    c = conn.cursor()
    c.execute("DELETE FROM chatbot_faq WHERE id=?", (id,))
    conn.commit()
    conn.close()
    
    load_chatbot_data()
    return jsonify({"success": True, "message": "FAQ supprimée"})

# ====== بدء التطبيق ======
if __name__ == '__main__':
    print("🚀 Démarrage de AutoLocation...")
    print("=" * 50)
    
    # تهيئة قاعدة البيانات
    init_db()
    print("✅ Base de données initialisée")
    
    # تحميل الشات بوت
    load_chatbot_data()
    print("✅ Chatbot intelligent chargé")
    
    print("=" * 50)
    print("🌐 Site client : http://localhost:5000")
    print("🔐 Admin login : http://localhost:5000/admin_login.html")
    print("🤖 Chatbot prêt avec TF-IDF + base véhicules")
    print("=" * 50)
    
    app.run(debug=True, port=5000, host='0.0.0.0')
    