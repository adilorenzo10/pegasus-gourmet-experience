import sqlite3, secrets, random, pytz, logging, os
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_assets import Environment, Bundle
from markupsafe import Markup
from sqlalchemy import and_, desc
from sqlalchemy.orm import joinedload
from database import SessionLocal
from models import Utente, Tavolo, Prenotazione, OrarioPrenotabile
from datetime import date, datetime, time, timezone
from babel.dates import format_date
from ajax import ajax
from passlib.context import CryptContext
from passlib import pwd
from decorators import with_db_session, login_required
from dotenv import load_dotenv


app = Flask(__name__)
app.register_blueprint(ajax, url_prefix="/ajax")

# Carica le variabili dal file .env
load_dotenv()  
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(16))

# Configura Flask-Assets
assets = Environment(app)

# Crea un bundle per il file Sass
scss = Bundle('scss/style.scss', filters='libsass', output='css/style.css')
assets.register('scss_all', scss)
scss.build() # Solo in fase di sviluppo

# Configuro il log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Homepage
@app.route("/")
@with_db_session
def index(db_session):
    user_id = session.get("user_id")
    
    utente = None
    if user_id:
        utente = db_session.query(Utente).filter_by(id=user_id).first()
    
    return render_template("index.html", utente=utente, header_transparent=True)

# Accedi
@app.route("/accedi", methods=["GET", "POST"])
@with_db_session
def accedi(db_session):
    titolo_pagina = "Accedi"
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
                
        # Cerca l'utente nel database
        utente = db_session.query(Utente).filter_by(email=email).first()
        if utente and utente.check_password(password):
            session["user_id"] = utente.id
            return redirect(url_for("index"))
        else:
            flash("Email o password non corretti. Riprova.", "danger")

    return render_template("accedi.html", titolo=titolo_pagina)

# Registrati
@app.route("/registrati", methods=["GET", "POST"])
@with_db_session
def registrati(db_session):
    titolo_pagina = "Registrati"
    
    if request.method == "POST":
        # Ottieni i dati dal form
        nome_ottenuto = request.form.get("nome")
        cognome_ottenuto = request.form.get("cognome")
        email_ottenuta = request.form.get("email")
        password_ottenuta = request.form.get("password")

        # Verifica se i campi obbligatori sono vuoti
        if not all([nome_ottenuto, cognome_ottenuto, email_ottenuta, password_ottenuta]):
            flash("Tutti i campi sono obbligatori.", "warning")
            return redirect(url_for("registrati"))

        # Controlla se l'utente esiste già
        utente = db_session.query(Utente).filter_by(email=email_ottenuta).first()
        if utente:
            flash("L'email è già in uso. Prova con un'altra o effettua l'accesso.", "danger")
            return redirect(url_for("registrati"))
        
        # Creazione nuovo utente
        try:
            nuovo_utente = Utente(
                nome=nome_ottenuto,
                cognome=cognome_ottenuto,
                email=email_ottenuta
            )
            nuovo_utente.set_password(password_ottenuta)  # Usa `set_password` per hashing e verifica robustezza
            db_session.add(nuovo_utente)
            db_session.commit()
            flash("La registrazione è stata completata con successo.", "success")
            return redirect(url_for("accedi"))

        except ValueError as e:
            flash(str(e), "danger")
            logger.error(f"Errore durante la creazione utente: {e}")
            return redirect(url_for("registrati"))
            
        except Exception as e:
            db_session.rollback()
            flash("Errore durante la registrazione", "danger")
            logger.error(f"Eccezione durante la registrazione: {e}")
            return redirect(url_for("registrati"))

    return render_template("registrati.html", titolo=titolo_pagina)

# Prenota o modifica un tavolo
@app.route("/prenota", methods=["GET", "POST"])
@app.route("/modifica-prenotazione/<int:prenotazione_id>", methods=["GET", "POST"])
@with_db_session
@login_required("Per favore accedi per prenotare un tavolo. Se non hai ancora un account, <a href='/registrati'>registrati</a> subito!")
def gestisci_prenotazione(db_session, prenotazione_id=None):
    titolo_pagina = "Prenotazione"
    user_id = session.get("user_id")
    data_corrente = datetime.now(pytz.timezone('Europe/Rome')).date()

    utente = db_session.query(Utente).filter_by(id=user_id).first()
    orari_prenotabili = db_session.query(OrarioPrenotabile).all()

    prenotazione = None
    if prenotazione_id:
        # Ricerca prenotazione esistente
        prenotazione = db_session.query(Prenotazione).filter_by(id=prenotazione_id, utente_id=user_id).first()
        if not prenotazione:
            flash("Prenotazione non trovata o non autorizzata.", "danger")
            return redirect(url_for("le_mie_prenotazioni"))

    if request.method == "POST":
        data = request.form.get("data")
        numero_persone = request.form.get("numero_persone")
        orario_prenotabile = request.form.get("orario")

        # Verifica campi obbligatori
        if not data or not orario_prenotabile:
            flash("Tutti i campi sono obbligatori.", "warning")
            return redirect(request.url)

        # Formatta e verifica data
        try:
            data_formattata = datetime.strptime(data, '%Y-%m-%d').date()
        except ValueError as e:
            flash("La data inserita non è valida.", "danger")
            return redirect(request.url)

        # Converti orario
        try:
            orario_prenotabile_id = int(orario_prenotabile)
        except ValueError:
            flash("Seleziona un orario valido.", "danger")
            return redirect(request.url)

        # Se è una nuova prenotazione o l'orario è stato modificato
        prenotazione_orario_prenotabile_id = getattr(prenotazione, "orario_prenotabile_id", None)
        if prenotazione is None or prenotazione_orario_prenotabile_id != orario_prenotabile_id:
            tavoli_non_prenotati = (
                db_session.query(Tavolo)
                .outerjoin(Prenotazione, and_(
                    Prenotazione.tavolo_id == Tavolo.id,
                    Prenotazione.data == data_formattata,
                    Prenotazione.orario_prenotabile_id == orario_prenotabile_id
                ))
                .filter(Prenotazione.id == None)
                .all()
            )
            if tavoli_non_prenotati:
                tavolo_id = random.choice(tavoli_non_prenotati).id
            else:
                flash("Nessun tavolo disponibile per la data e l'orario selezionati.", "warning")
                return redirect(request.url)
        else:
            tavolo_id = prenotazione.tavolo_id
        try:
            # Creazione o aggiornamento prenotazione
            if prenotazione:
                setattr(prenotazione, 'data', data_formattata)
                setattr(prenotazione, 'numero_persone', numero_persone)
                setattr(prenotazione, 'orario_prenotabile_id', orario_prenotabile_id)
                setattr(prenotazione, 'tavolo_id', tavolo_id)
                flash("La prenotazione è stata modificata.", "success")
            else:
                nuova_prenotazione = Prenotazione(
                    data=data_formattata,
                    numero_persone=numero_persone,
                    utente_id=user_id,
                    tavolo_id=tavolo_id,
                    orario_prenotabile_id=orario_prenotabile_id
                )
                db_session.add(nuova_prenotazione)        
                flash("La prenotazione è stata accettata.", "success")

            db_session.commit()
            return redirect(url_for("le_mie_prenotazioni"))

        except Exception as e:
            db_session.rollback()
            flash(f"Errore durante la prenotazione", "danger")
            logger.error(f"Errore durante la prenotazione: {e}")


    return render_template("gestisci_prenotazione.html", utente=utente, orari=orari_prenotabili, today=data_corrente, prenotazione=prenotazione, titolo=titolo_pagina)

# Le mie prenotazioni
@app.route("/le-mie-prenotazioni")
@with_db_session
@login_required("Per favore accedi per visualizzare le tue prenotazioni. Se non hai ancora un account, <a href='/registrati'>registrati</a> subito!")
def le_mie_prenotazioni(db_session):
    titolo_pagina = "Le mie prenotazioni"
    user_id = session.get("user_id")
    data_corrente = datetime.now(pytz.timezone('Europe/Rome'))

    # Crea una sessione con il database e recupera i dati utente
    try:
        mie_prenotazioni = (
            db_session.query(Prenotazione)
            .filter_by(utente_id=user_id)
            .join(OrarioPrenotabile, Prenotazione.orario_prenotabile_id == OrarioPrenotabile.id)
            .join(Tavolo, Prenotazione.tavolo_id == Tavolo.id)
            .options(
                joinedload(Prenotazione.orario),  # Carica l'orario della prenotazione
                joinedload(Prenotazione.tavolo)   # Carica il tavolo della prenotazione
            )
            .order_by(desc(Prenotazione.data), desc(OrarioPrenotabile.orario))  # Ordinamento per data e orario decrescenti
            .all()
        )
    except ValueError:
        flash("Seleziona un orario valido.", "danger")
        return redirect(url_for("prenota"))
    
    return render_template("le_mie_prenotazioni.html", prenotazioni = mie_prenotazioni, data_corrente = data_corrente, titolo=titolo_pagina)

# Modifica profilo
@app.route("/modifica-profilo", methods=["GET", "POST"])
@with_db_session
@login_required("Sei stato disconnesso, per favore, effettua di nuovo l'accesso.")
def modifica_profilo(db_session):
    titolo_pagina = "Modifica profilo"
    user_id = session.get("user_id")
    utente = db_session.query(Utente).filter_by(id=user_id).first()

    if not utente:
        flash("Dati utente non trovati.", "danger")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        nome = request.form.get("nome")
        cognome = request.form.get("cognome")
        email = request.form.get("email")
        
        setattr(utente, 'nome', nome)
        setattr(utente, 'cognome', cognome)
        setattr(utente, 'email', email)

        if request.form.get("password-attuale") and request.form.get("password"):
            password_attuale = request.form.get("password-attuale")
            nuova_password = request.form.get("password")

            if not utente.check_password(password_attuale):
                flash("La password attuale è errata.", "danger")
                return redirect(url_for("modifica_profilo"))

            try:
                utente.set_password(nuova_password)
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("modifica_profilo"))

        try:
            db_session.commit()
            flash("Il profilo è stato aggiornato con successo.", "success")
        except Exception as e:
            db_session.rollback()
            flash("Errore durante l'aggiornamento del profilo.", "danger")
            logger.error(f"Eccezione generata durante l'aggiornamento del profilo: {e}")

        return redirect(url_for("modifica_profilo"))

    return render_template("modifica_profilo.html", utente=utente, titolo=titolo_pagina)

# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logout effettuato con successo!", "success")
    return redirect(url_for("accedi"))

# Gestione errore 404
@app.errorhandler(404)
def page_not_found(e):
    titolo_pagina="Errore 404 - Pagina non trovata"
    return render_template("404.html", titolo=titolo_pagina), 404

# Filtro data formattata
@app.template_filter("data_formattata")
def data_formattata(data):
    return format_date(data, "EE dd MMM YYYY", locale="it_IT")

# Titolo default per ogni template
@app.context_processor
def inject_default_title():
    return dict(titolo_default="Pegasus Gourmet Experience")