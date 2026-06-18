from typing import Dict, Any


def _rens_isbn(isbn: str) -> str:
    if not isbn:
        raise ValueError("ISBN mangler.")
    # fjerner mellomrom og bindestreker
    cleaned = isbn.replace("-", "").replace(" ", "").strip()
    if not cleaned:
        raise ValueError("ISBN mangler.")
    return cleaned


async def hent_bokdata_fra_isbn(cursor, isbn: str) -> Dict[str, Any]:
    isbn = _rens_isbn(isbn)

    sql = """
        SELECT
            boktittel,
            forfatter,
            utgitt,
            forlag,
            merknad,
            isbn
        FROM `db_oslomet`.`filoversikt_unike_titler`
        WHERE isbn = %s
        LIMIT 1
    """

    await cursor.execute(sql, (isbn,))
    row = await cursor.fetchone()

    if not row:
        return {
            "found": False,
            "data": None,
            "message": "Ingen bok funnet for oppgitt ISBN."
        }

    return {
        "found": True,
        "data": {
            "boktittel": row.get("boktittel") or "",
            "forfatter": row.get("forfatter") or "",
            "utgitt": row.get("utgitt") or "",
            "forlag": row.get("forlag") or "",
            "merknad": row.get("merknad") or "",
            "isbn": row.get("isbn") or "",
        }
    }
