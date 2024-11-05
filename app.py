import random
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_assets import Environment, Bundle
from markupsafe import Markup
from sqlalchemy import and_ 
from database import SessionLocal
from models import Utente, Tavolo, Prenotazione, OrarioPrenotabile
from datetime import date, datetime, time
from ajax import ajax
import sqlite3, secrets
from sqlalchemy.orm import joinedload


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



# Prenota un tavolo
@app.route("/prenota", methods=["GET", "POST"])
def prenota():
    user_id = session.get("user_id")

    # Se l'utente non è loggato, reindirizza alla pagina di accesso
    if not user_id:
        flash(Markup("Per favore accedi per prenotare un tavolo. Se non hai ancora un account, <a href='/registrati'>registrati</a> subito!"), "warning")
        return redirect(url_for("accedi"))

    # Crea una sessione con il database e recupera i dati utente
    db_session = SessionLocal()
    try:
        utente = db_session.query(Utente).filter_by(id=user_id).first()
        orari_prenotabili = db_session.query(OrarioPrenotabile).all()

        # Azioni da svolgere inviando il form di prenotazione
        if request.method == "POST":
            # Dati prenotazione
            data = request.form.get("data")
            orario_prenotabile = request.form.get("orario")
            tavolo_id = 1

            # Verifica campi obbligatori e formato della data
            if not data or not orario_prenotabile:
                flash("Tutti i campi sono obbligatori.", "warning")
                return redirect(url_for("prenota"))


            try:
                tavoli_non_prenotati = (
                    db_session.query(Tavolo)
                    .outerjoin(Prenotazione, and_(
                        Prenotazione.tavolo_id == Tavolo.id,
                        Prenotazione.data == data,
                        Prenotazione.orario_prenotabile_id == orario_prenotabile
                    ))
                    .filter(Prenotazione.id == None)
                    .all()
                )
                if tavoli_non_prenotati:
                    # Ricava random un id dei tavoli non prenotati
                    tavolo_id = random.choice(tavoli_non_prenotati).id
                else:
                    # Gestisci il caso in cui non ci siano tavoli disponibili
                    flash("Nessun tavolo disponibile per la data e l'orario selezionati.", "warning")
                    return redirect(url_for("prenota"))

            except ValueError:
                flash("Errore nella query per ottenere i tavoli non prenotati.", "danger")
                return redirect(url_for("prenota"))
            
            try:
                data_formattata = datetime.strptime(data, '%Y-%m-%d').date()

            except ValueError:
                flash("La data inserita non è valida.", "danger")
                return redirect(url_for("prenota"))

            # Converti orario_prenotabile in intero
            try:
                orario_prenotabile_id = int(orario_prenotabile)
            except ValueError:
                flash("Seleziona un orario valido.", "danger")
                return redirect(url_for("prenota"))

            try:
                # Crea la nuova prenotazione
                nuova_prenotazione = Prenotazione(
                    data=data_formattata,
                    utente_id=user_id,
                    tavolo_id=tavolo_id,
                    orario_prenotabile_id=orario_prenotabile_id
                )

                db_session.add(nuova_prenotazione)        
                db_session.commit()
                flash("La prenotazione è stata accettata, puoi visualizzare tutte le tue prenotazioni nell'area utente.", "success")
                return redirect(url_for("prenota"))
            except Exception as e:
                db_session.rollback()
                flash(f"Errore durante la prenotazione: {e}", "danger")
    finally:
        db_session.close()

    # Passa i dati dell'utente e gli orari al template
    return render_template("prenota.html", utente=utente, orari=orari_prenotabili)
    

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
            .all()
        )
    except ValueError:
                flash("Seleziona un orario valido.", "danger")
                return redirect(url_for("prenota"))
    finally:
        db_session.close()
    
    return render_template("le_mie_prenotazioni.html", prenotazioni = mie_prenotazioni)

# Modifica profilo
@app.route("/modifica-profilo")
def modifica_profilo():
    return render_template("modifica_profilo.html")

# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logout effettuato con successo!", "success")
    return redirect(url_for("accedi"))