import random
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_assets import Environment, Bundle
from markupsafe import Markup
import pytz
from sqlalchemy import and_, desc 
from database import SessionLocal
from models import Utente, Tavolo, Prenotazione, OrarioPrenotabile
from datetime import date, datetime, time, timezone
from ajax import ajax
import sqlite3, secrets
from sqlalchemy.orm import joinedload
from babel.dates import format_date


app = Flask(__name__)
app.register_blueprint(ajax, url_prefix="/ajax")
app.secret_key = secrets.token_hex(16)

# Configura Flask-Assets
assets = Environment(app)

# Crea un bundle per il file Sass
scss = Bundle('scss/style.scss', filters='libsass', output='css/style.css')
assets.register('scss_all', scss)
scss.build() # Solo in fase di sviluppo

# Homepage
@app.route("/")
def index():
    return render_template("index.html")

# Accedi
@app.route("/accedi", methods=["GET", "POST"])
def accedi():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        db_session = SessionLocal()
        
        # Cerca l'utente nel database
        utente = db_session.query(Utente).filter_by(email=email).first()
        if utente and utente.check_password(password):
            session["user_id"] = utente.id
            #flash("Login effettuato con successo!", "success")
            return redirect(url_for("index"))
        else:
            flash("Email o password non corretti. Riprova.", "danger")
        
        # Chiudi la sessione del database
        db_session.close()

    return render_template("accedi.html")

# Registrati
@app.route("/registrati", methods=["GET", "POST"])
def registrati():
    if request.method == "POST":
        nome_ottenuto = request.form.get("nome")
        cognome_ottenuto = request.form.get("cognome")
        email_ottenuta = request.form.get("email")
        password_ottenuta = request.form.get("password")


        # Verifica se i campi obbligatori sono vuoti
        if not all([nome_ottenuto, cognome_ottenuto, email_ottenuta, password_ottenuta]):
            flash("Tutti i campi sono obbligatori.", "warning")
            return redirect(url_for("registrati"))
        
        
        # Cerca l'utente nel database
        db_session = SessionLocal()
        utente = db_session.query(Utente).filter_by(email=email_ottenuta).first()
        if not utente:
                try:
                    nuovo_utente = Utente(nome=nome_ottenuto, cognome=cognome_ottenuto, email=email_ottenuta)
                    nuovo_utente.set_password(password_ottenuta)
                    db_session.add(nuovo_utente)        
                    db_session.commit()
                    flash("La registrazione è stata completata con successo, adesso puoi accedere al sito per effettuare una prenotazione.", "success")
                    return redirect(url_for("accedi"))
                except Exception as e:
                    db_session.rollback()
                    flash(f"Errore durante la registrazione: {e}", "danger")
                finally:
                    db_session.close()
        else:
            flash("L'email inserita è già stata utilizzata. Riprova con un'altra oppure effettua l'accesso.", "danger")
                
    return render_template("registrati.html")

# Prenota o modifica un tavolo
@app.route("/prenota", methods=["GET", "POST"])
@app.route("/modifica-prenotazione/<int:prenotazione_id>", methods=["GET", "POST"])
def gestisci_prenotazione(prenotazione_id=None):
    user_id = session.get("user_id")
    today = datetime.now(timezone.utc).date()

    if not user_id:
        flash(Markup("Per favore accedi per prenotare un tavolo. Se non hai ancora un account, <a href='/registrati'>registrati</a> subito!"), "warning")
        return redirect(url_for("accedi"))

    db_session = SessionLocal()
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
        except ValueError:
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
            flash(f"Errore durante la prenotazione: {e}", "danger")

        finally:
            db_session.close()
    return render_template("gestisci_prenotazione.html", utente=utente, orari=orari_prenotabili, today=today, prenotazione=prenotazione)    

# Chi siamo
@app.route("/chi-siamo")
def chi_siamo():
    return render_template("chi_siamo.html")

# Il mio account
@app.route("/il-mio-account")
def il_mio_account():
    return render_template("il_mio_account.html")

# Le mie prenotazioni
@app.route("/le-mie-prenotazioni")
def le_mie_prenotazioni():
    user_id = session.get("user_id")
    data_corrente = datetime.now(pytz.timezone('Europe/Rome'))

    # Se l'utente non è loggato, reindirizza alla pagina di accesso
    if not user_id:
        flash(Markup("Per favore accedi per visualizzare le tue prenotazioni. Se non hai ancora un account, <a href='/registrati'>registrati</a> subito!"), "warning")
        return redirect(url_for("accedi"))

    # Crea una sessione con il database e recupera i dati utente
    db_session = SessionLocal()
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
    finally:
        db_session.close()
    
    return render_template("le_mie_prenotazioni.html", prenotazioni = mie_prenotazioni, data_corrente = data_corrente)

# Modifica profilo
@app.route("/modifica-profilo", methods=["GET", "POST"])
def modifica_profilo():
    user_id = session.get("user_id")

    # Se l'utente non è loggato, reindirizza alla pagina di accesso
    if not user_id:
        flash(Markup("Sei stato disconnesso, per favore, effettua di nuovo l'accesso. Se non hai un account, <a href='/registrati'>registrati</a> subito!"), "warning")
        return redirect(url_for("accedi"))

    # Crea una sessione con il database e recupera i dati utente
    db_session = SessionLocal()
    utente = db_session.query(Utente).filter_by(id=user_id).first()

    if not utente:
        flash("Dati utente non trovati.", "danger")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        # Recupera i dati dal form
        nome = request.form.get("nome")
        cognome = request.form.get("cognome")
        email = request.form.get("email")

        # Aggiorna i dati utente
        setattr(utente, 'nome', nome)
        setattr(utente, 'cognome', cognome)
        setattr(utente, 'email', email)

        # Se l'utente desidera cambiare la password
        if request.form.get("password-attuale") and request.form.get("password"):
            password_attuale = request.form.get("password-attuale")
            nuova_password = request.form.get("password")

            # Verifica la password attuale
            if not utente.check_password(password_attuale):
                flash("La password attuale è errata.", "danger")
                return redirect(url_for("modifica_profilo"))

            # Imposta la nuova password
            utente.set_password(nuova_password)

        # Salva le modifiche nel database
        try:
            db_session.commit()
            flash("Il profilo è stato aggiornato con successo.", "success")
        except Exception as e:
            db_session.rollback()
            flash(f"Errore durante l'aggiornamento del profilo: {e}", "danger")
        finally:
            db_session.close()

        return redirect(url_for("modifica_profilo"))

    # GET: Mostra il form di modifica profilo con i dati utente
    return render_template("modifica_profilo.html", utente=utente)

# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logout effettuato con successo!", "success")
    return redirect(url_for("accedi"))

# Filtro data formattata
@app.template_filter("data_formattata")
def data_formattata(data):
    return format_date(data, "EE dd MMM YYYY", locale="it_IT")