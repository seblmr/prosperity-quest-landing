import logging
from datetime import date
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy import create_engine, Column, Integer, String, Date, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ ERREUR : TOKEN non trouvé dans .env")
    print("Vérifie que le fichier .env existe et contient exactement : TOKEN=tonvrai_token")
    exit()

print("✅ Token chargé avec succès !")
print("🚀 Prosperity.Quest Bot démarré !")
# ================= (le reste du code reste IDENTIQUE) =================
DB = "prosperity.db"

# Base de données simple
Base = declarative_base()
engine = create_engine(f"sqlite:///{DB}")
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    completed_quests = Column(JSON, default=list)
    last_daily = Column(Date)

Base.metadata.create_all(engine)

# ================= QUÊTES (30 premières prêtes) =================
QUESTS = [
    # Jour 1 à 30 - tu peux en ajouter à l'infini
    {"id": 1, "kingdom": "Mindset", "title": "🌟 Affirmation Légendaire", "desc": "Écris 10x : « Je suis un aimant à prospérité » et poste en story (anonyme OK).", "xp": 50},
    {"id": 2, "kingdom": "Savoir", "title": "📖 Lecture du Roi", "desc": "Lis 10 pages de « Père riche, père pauvre » ou écoute 15 min de podcast finance.", "xp": 40},
    {"id": 3, "kingdom": "Action", "title": "💰 Compte d’abondance", "desc": "Ouvre un compte épargne / Trade Republic et verse 5 € minimum.", "xp": 80},
    {"id": 4, "kingdom": "Abondance", "title": "🔥 Partage ta flamme", "desc": "Invite 1 pote sur @ProsperityQuestBot avec ton lien perso.", "xp": 60},
    {"id":5,"kingdom":"Mindset","title":"🪄 Gratitude 1 %","desc":"Liste 5 choses pour lesquelles tu es déjà riche.","xp":30},
    {"id":6,"kingdom":"Savoir","title":"💡 Side-hustle idea","desc":"Trouve 3 idées de side-hustle à moins de 50 €.","xp":70},
    {"id":7,"kingdom":"Action","title":"📉 Net Worth Day","desc":"Calcule ton patrimoine net (actifs - dettes).","xp":100},
    {"id":8,"kingdom":"Abondance","title":"🎟️ Ticket de loto mental","desc":"Achète un vrai ticket de loto ET visualise le gain.","xp":45},
    {"id":9,"kingdom":"Mindset","title":"🛡️ Bouclier anti-doute","desc":"Réponds à 1 peur financière par écrit.","xp":55},
    {"id":10,"kingdom":"Savoir","title":"📱 Follow 5 comptes","desc":"Suis 5 comptes finance/mindset sur X ou Insta.","xp":35},
    {"id":11,"kingdom":"Action","title":"🛒 No-spend 24h","desc":"24h sans dépense inutile (sauf nourriture).","xp":90},
    {"id":12,"kingdom":"Abondance","title":"📤 Parrainage x2","desc":"Fais rejoindre 2 potes au bot.","xp":120},
    {"id":13,"kingdom":"Mindset","title":"📜 Lettre au futur toi","desc":"Écris une lettre à ton toi dans 1 an millionnaire.","xp":65},
    {"id":14,"kingdom":"Savoir","title":"📊 Budget 80/20","desc":"Applique la règle 80/20 sur tes dépenses.","xp":50},
    {"id":15,"kingdom":"Action","title":"🚀 Vente flash","desc":"Vends 1 objet sur Vinted/Leboncoin (>20 €).","xp":110},
    {"id":16,"kingdom":"Abondance","title":"🌍 Don 1 %","desc":"Donne 1 % de tes revenus du mois à une cause.","xp":40},
    {"id":17,"kingdom":"Mindset","title":"🔥 Burn the boats","desc":"Supprime 1 app qui te fait perdre du temps.","xp":70},
    {"id":18,"kingdom":"Savoir","title":"🎙️ Écoute riche","desc":"Écoute 20 min d’interview d’un millionnaire.","xp":45},
    {"id":19,"kingdom":"Action","title":"📈 Invest 10 €","desc":"Achète ta première action ou crypto.","xp":95},
    {"id":20,"kingdom":"Abondance","title":"🏆 Leaderboard","desc":"Poste ton niveau dans le groupe public.","xp":80},
    {"id":21,"kingdom":"Mindset","title":"🧬 Identité riche","desc":"Change ton bio : « En route vers 7 chiffres »","xp":60},
    {"id":22,"kingdom":"Savoir","title":"🧾 Facture mentale","desc":"Crée ta première facture pour un futur client.","xp":55},
    {"id":23,"kingdom":"Action","title":"⏰ Deep work 60 min","desc":"60 min focus sur un side-hustle.","xp":85},
    {"id":24,"kingdom":"Abondance","title":"🤝 Réseau","desc":"Envoie 1 message DM à quelqu’un qui t’inspire.","xp":50},
    {"id":25,"kingdom":"Mindset","title":"🌕 Pleine lune money","desc":"Rituel : visualise l’argent qui coule vers toi.","xp":40},
    {"id":26,"kingdom":"Savoir","title":"📚 Livre chapitre 2","desc":"Continue le livre commencé.","xp":35},
    {"id":27,"kingdom":"Action","title":"📦 Micro-produit","desc":"Crée un produit digital à vendre 9 €.","xp":130},
    {"id":28,"kingdom":"Abondance","title":"🎉 Célébration","desc":"Célèbre une petite victoire financière.","xp":45},
    {"id":29,"kingdom":"Mindset","title":"🧠 10 affirmations","desc":"Répète 10 affirmations de richesse.","xp":55},
    {"id":30,"kingdom":"Savoir","title":"📈 Analyse 1 investissement","desc":"Étudie 1 action ou crypto en profondeur.","xp":75}
]


# Pour l’instant on en met 30, mais je te donne tout le pack ci-dessous

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        user = User(user_id=user_id, username=update.effective_user.username)
        session.add(user)
        session.commit()
    await update.message.reply_text(
        f"🗡️ Bienvenue dans **Prosperity.Quest**, {update.effective_user.first_name} !\n\n"
        "Tu es niveau 1. Ta quête commence aujourd’hui.\n"
        "Tape /dailyquest pour ta mission du jour."
    )
    session.close()

async def dailyquest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    
    today = date.today()
    if user.last_daily == today:
        await update.message.reply_text("✅ Tu as déjà reçu ta quête du jour, aventurier ! Reviens demain.")
        session.close()
        return
    
    # Choisit une quête non terminée (simple rotation)
    quest_index = len(user.completed_quests) % len(QUESTS)
    quest = QUESTS[quest_index]
    
    keyboard = [["✅ Je l’ai fait !"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        f"**Quête du jour #{quest['id']} — {quest['kingdom']}**\n\n"
        f"**{quest['title']}**\n{quest['desc']}\n\n"
        f"Récompense : +{quest['xp']} XP",
        reply_markup=reply_markup
    )
    session.close()

async def complete_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != "✅ Je l’ai fait !":
        return
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    
    today = date.today()
    quest_index = len(user.completed_quests) % len(QUESTS)
    quest = QUESTS[quest_index]
    
    user.xp += quest["xp"]
    user.completed_quests.append(quest["id"])
    user.last_daily = today
    
    # Level up ?
    new_level = (user.xp // 300) + 1
    if new_level > user.level:
        user.level = new_level
        await update.message.reply_text(f"🎉 LEVEL UP ! Tu es maintenant niveau **{new_level}** !")
    
    await update.message.reply_text(f"✅ Quête validée ! +{quest['xp']} XP. Tape /progress pour voir ta progression.")
    session.commit()
    session.close()

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    session.close()
    
    await update.message.reply_text(
        f"📊 **Ton avancement**\n\n"
        f"🏆 Niveau : {user.level}\n"
        f"⭐ XP : {user.xp} / {(user.level * 300)}\n"
        f"✅ Quêtes terminées : {len(user.completed_quests)}\n"
        f"🔥 Streak : {user.last_daily.strftime('%d/%m') if user.last_daily else '0'}"
    )

# ================= LANCEMENT =================
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dailyquest", dailyquest))
    app.add_handler(CommandHandler("progress", progress))
    app.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, complete_quest))
    
    print("🚀 Prosperity.Quest Bot démarré !")
    app.run_polling()

if __name__ == "__main__":
    main()
