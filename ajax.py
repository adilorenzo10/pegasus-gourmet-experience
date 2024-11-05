from flask import Blueprint, jsonify, request
from database import SessionLocal
from models import OrarioPrenotabile, Prenotazione
from datetime import datetime

ajax = Blueprint("ajax", __name__)

@ajax.route("/orari_disponibili", methods=["POST"])
def orari_disponibili():
    data_selezionata = request.json.get("data") # type: ignore
    db_session = SessionLocal()

    # Codice per ottenere orari non prenotati
    orari_prenotati = db_session.query(Prenotazione.orario_prenotabile_id).filter_by(data=data_selezionata).all()
    orari_prenotati_ids = [orario[0] for orario in orari_prenotati]
    orari_disponibili = db_session.query(OrarioPrenotabile).filter(~OrarioPrenotabile.id.in_(orari_prenotati_ids)).all()

    print("Data selezionata:", data_selezionata)
    print("Orari prenotati:", orari_prenotati_ids)

    db_session.close()

    # Converti orari in JSON
    orari_disponibili_dict = [{"id": orario.id, "orario": orario.orario.strftime("%H:%M")} for orario in orari_disponibili]
    return jsonify(orari_disponibili_dict)
