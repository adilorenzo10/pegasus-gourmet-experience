from flask import Blueprint, jsonify, request
from database import SessionLocal
from models import OrarioPrenotabile, Prenotazione
from datetime import datetime

ajax = Blueprint("ajax", __name__)

@ajax.route("/orari_disponibili", methods=["POST"])
def orari_disponibili():
    data_selezionata = request.json.get("data") # type: ignore
    db_session = SessionLocal()

    # Ottieni orari disponibili
    orari_prenotati = db_session.query(Prenotazione.orario_prenotabile_id).filter_by(data=data_selezionata).all()
    orari_prenotati_ids = [orario[0] for orario in orari_prenotati]
    orari_disponibili = db_session.query(OrarioPrenotabile).filter(~OrarioPrenotabile.id.in_(orari_prenotati_ids)).all()

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
