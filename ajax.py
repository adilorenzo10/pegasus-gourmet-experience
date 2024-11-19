from flask import Blueprint, jsonify, request, session
from database import SessionLocal
from models import OrarioPrenotabile, Prenotazione, Tavolo
from datetime import datetime

ajax = Blueprint("ajax", __name__)

@ajax.route("/orari_disponibili", methods=["POST"])
def orari_disponibili():
    data_selezionata = request.json.get("data") # type: ignore
    db_session = SessionLocal()

    # Ottieni il numero totale di tavoli
    totale_tavoli = db_session.query(func.count(Tavolo.id)).scalar()

    # Ottieni gli orari prenotati e il conteggio delle prenotazioni per la data selezionata
    orari_conteggio = (
        db_session.query(Prenotazione.orario_prenotabile_id, func.count(Prenotazione.id).label("conteggio"))
        .filter(Prenotazione.data == data_selezionata)
        .group_by(Prenotazione.orario_prenotabile_id)
        .all()
    )

    # Identifica gli orari da escludere (quelli con un conteggio >= totale_tavoli)
    orari_esclusi = [
        orario[0] for orario in orari_conteggio if orario.conteggio >= totale_tavoli
    ]
    
    # Ottieni solo gli orari non esclusi
    orari_disponibili = db_session.query(OrarioPrenotabile).filter(~OrarioPrenotabile.id.in_(orari_esclusi)).all()
    db_session.close()

    # Converti orari in JSON
    orari_disponibili_dict = [{"id": orario.id, "orario": orario.orario.strftime("%H:%M")} for orario in orari_disponibili]
    return jsonify(orari_disponibili_dict)


@ajax.route("/cancella_prenotazione", methods=["POST"])
def cancella_prenotazione():
    id_prenotazione = request.json.get("id_prenotazione")  # type: ignore
    db_session = SessionLocal()

    try:
        # Cerca la prenotazione nel database
        prenotazione = db_session.query(Prenotazione).filter_by(id=id_prenotazione).first()
        if prenotazione:
            # Rimuovi la prenotazione
            db_session.delete(prenotazione)
            db_session.commit()
            esito = {"success": True, "id": id_prenotazione, "message": "Prenotazione cancellata con successo."}
        else:
            esito = {"success": False, "message": "Prenotazione non trovata."}
    except Exception as e:
        db_session.rollback()
        esito = {"success": False, "message": f"Errore: {e}"}
    finally:
        db_session.close()

    return jsonify(esito)

@ajax.route("/verifica_data_prenotazione", methods=["POST"])
def verifica_data_prenotazione():
    data_selezionata = request.json.get("data")  # type: ignore
    user_id = session.get("user_id")

    db_session = SessionLocal()

    try:
        # Ottieni prenotazioni utente nella data selezionata
        prenotazioni = db_session.query(Prenotazione).filter_by(data=data_selezionata, utente_id=user_id).all()
        if prenotazioni:
            return jsonify({"prenotazione_esiste": True})
        else:
            return jsonify({"prenotazione_esiste": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db_session.close()


from sqlalchemy import func
