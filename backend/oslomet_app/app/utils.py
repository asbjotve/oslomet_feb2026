import decimal
import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def convert_types(obj):
    """Konverterer Decimal til float og datoer til isoformat, rekursivt i lister og dicts."""
    if isinstance(obj, list):
        return [convert_types(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_types(v) for k, v in obj.items()}
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    else:
        return obj

def update_sidetall(fil1_data, fil2_path):
    """Oppdaterer 'sidetall' på fil1_data basert på mms_id i fil2_path (json-fil)."""
    # Finn absolutt sti til fil2_path, relativt til denne filen
    project_root = Path(__file__).resolve().parents[1]
    fil2_abs = project_root / "data" / fil2_path
    try:
        with fil2_abs.open("r", encoding="utf-8") as f:
            fil2_data = json.load(f)
    except Exception as e:
        logger.error("Kunne ikke åpne eller lese %s: %s", fil2_abs, e)
        return fil1_data

    fil2_dict = {
        str(item["mms_id"]): item["sidetall"]
        for item in fil2_data
        if "mms_id" in item and "sidetall" in item
    }
    logger.debug("mms_id-er i fil2.json: %s", list(fil2_dict.keys()))
    debug_hits = 0
    for item in fil1_data:
        mms_id = str(item.get("mms_id"))
        logger.debug("mms_id fra DB: '%s'", mms_id)
        if mms_id and mms_id in fil2_dict:
            item["sidetall"] = fil2_dict[mms_id]
            logger.debug("Treffer! Setter sidetall=%s for mms_id=%s", fil2_dict[mms_id], mms_id)
            debug_hits += 1
        else:
            item["sidetall"] = None
            logger.debug("Ingen sidetall for mms_id=%s", mms_id)
    logger.info("Antall treff på sidetall: %d av %d", debug_hits, len(fil1_data))
    return fil1_data
