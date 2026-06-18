from typing import Any, Dict, List, Literal, Sequence

import aiomysql

ReferanseType = Literal["fikses", "nye", "alle"]

SQL_KOPINOR_REFERANSER_FOR_PENSUMLISTE = """
SELECT
    api_alma_referanser.id,
    api_alma_referanser.file_link,
    sammensatt_sideangivelse AS 'Sideangivelse fra Alma',
    sideangivelse,
    filoversikt_data.mange_sideangivelser,
    api_alma_referanser.isbn AS ISBN
FROM
    api_alma_referanser
LEFT JOIN
    filoversikt_data ON api_alma_referanser.file_link = filoversikt_data.filnavn
WHERE
    api_alma_referanser.pensumliste_id = %s
    AND api_alma_referanser.bolk_rapp_indikator IN ({indikator_placeholders})
    AND api_alma_referanser.secondary_type IN ('Book', 'Book Chapter', 'Book Extract')
"""


def _indikatorer_for_type(t: ReferanseType) -> Sequence[int]:
    if t == "nye":
        return (5, 6)
    if t == "fikses":
        return (3, 4, 7)
    if t == "alle":
        return (3, 4, 5, 6, 7)
    raise ValueError(f"Ugyldig type: {t}")


async def fetch_kopinor_referanser_for_pensumliste(
    cursor: aiomysql.DictCursor,
    *,
    pensumliste_id: int,
    type: ReferanseType,
) -> List[Dict[str, Any]]:
    indikatorer = list(_indikatorer_for_type(type))
    placeholders = ", ".join(["%s"] * len(indikatorer))

    sql = SQL_KOPINOR_REFERANSER_FOR_PENSUMLISTE.format(
        indikator_placeholders=placeholders
    )

    params = (pensumliste_id, *indikatorer)

    await cursor.execute(sql, params)
    rows = await cursor.fetchall()
    return list(rows)
