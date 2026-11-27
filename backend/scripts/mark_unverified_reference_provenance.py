"""Replace unsupported public reference-source/license claims with honest status."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.database import get_db_connection

EXPECTED_SOURCES = {
    "sa-devanagari": "StrokeSpeak Standard Sanskrit Orthography Engine (NCERT High-Fidelity)",
    "ta": "StrokeSpeak Standard Tamil Orthography Engine (High-Fidelity)",
    "zh-hans": "StrokeSpeak Standard Chinese (Simplified) Orthography Engine",
}
NEW_SOURCE = "StrokeSpeak local draft data (source attribution pending)"
NEW_LICENSE = "Provenance unverified; do not redistribute"


def update_provenance_labels():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    changed = 0
    try:
        connection.start_transaction()
        cursor.execute(
            """SELECT c.id, l.script_code, c.reference_strokes_svg
               FROM characters c JOIN languages l ON l.id=c.language_id
               WHERE l.script_code IN (%s,%s,%s) AND c.reference_strokes_svg IS NOT NULL
               FOR UPDATE""",
            tuple(EXPECTED_SOURCES),
        )
        rows = cursor.fetchall()
        for row in rows:
            data = row["reference_strokes_svg"]
            if isinstance(data, str):
                data = json.loads(data)
            if data.get("provenance_status") == "unverified":
                continue
            if data.get("source") != EXPECTED_SOURCES[row["script_code"]]:
                raise RuntimeError(f"Unexpected source label on public character {row['id']}; refusing partial update.")
            previous_source = data.get("source")
            previous_license = data.get("license")
            data["source"] = NEW_SOURCE
            data["license"] = NEW_LICENSE
            data["provenance_status"] = "unverified"
            data["previous_source_label"] = previous_source
            data["previous_license_label"] = previous_license
            cursor.execute(
                "UPDATE characters SET reference_strokes_svg=%s WHERE id=%s",
                (json.dumps(data, ensure_ascii=False), row["id"]),
            )
            changed += 1
        connection.commit()
        print(f"Updated provenance labels for {changed} public reference records. Stroke vectors were untouched.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    update_provenance_labels()
