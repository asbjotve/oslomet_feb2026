from typing import Any, List, Optional, Tuple

from app.services.kopinor.kopinor_filters import Variant, map_fakultet, variant_clause

SQL_BASE = """
SELECT
    KursPensumlisteView.code as kurskode,
    KursPensumlisteView.pensumliste_id,
    KursPensumlisteView.aarsem,
    total_referanser_rapporteringspliktig,
    antall_bolket,
    antall_skal_bolkes,
    antall_declined,
    antall_annen_status,
    bestiller,
    kopinor_rapport.status,
    CASE
        WHEN total_referanser_rapporteringspliktig = antall_bolket THEN 1
        ELSE 0
    END AS `Liste skal låses`,
    antall_ref_ubehandlet
FROM KursPensumlisteView
JOIN kopinor_rapportering_tall
    ON kopinor_rapportering_tall.pensumliste_id = KursPensumlisteView.pensumliste_id
LEFT JOIN kopinor_rapport
    ON KursPensumlisteView.pensumliste_id = kopinor_rapport.pensumliste_id
WHERE
    {aarsem_clause}
    {pensumliste_clause}
    AND kobling IS NULL
    AND total_referanser_rapporteringspliktig > 0
    {fakultet_clause}
    {variant_clause}
    AND (
        kopinor_rapport.status IS NULL
        OR kopinor_rapport.status NOT IN ('Bestilt og levert', 'I bestilling, men ikke levert')
    )
GROUP BY KursPensumlisteView.pensumliste_id
"""


def build_kopinor_tall_sql(
    *,
    aarsem: str,
    fakultet: str,
    variant: Variant,
    partial_aarsem: bool = False,
    pensumliste_id: Optional[int] = None,
) -> Tuple[str, tuple]:
    """
    Bygger SQL + params.

    - aarsem: eksakt eller prefix (partial_aarsem)
    - pensumliste_id: hvis satt -> AND KursPensumlisteView.pensumliste_id = %s
    """
    aarsem_clean = (aarsem or "").strip()
    params: List[Any] = []

    # aarsem
    if partial_aarsem:
        aarsem_clause = "KursPensumlisteView.aarsem LIKE %s"
        params.append(f"{aarsem_clean}%")
    else:
        aarsem_clause = "KursPensumlisteView.aarsem = %s"
        params.append(aarsem_clean)

    # pensumliste (valgfri)
    if pensumliste_id is None:
        pensumliste_clause = ""
    else:
        pensumliste_clause = "AND KursPensumlisteView.pensumliste_id = %s"
        params.append(pensumliste_id)

    # fakultet
    fakulteter = map_fakultet(fakultet)
    if fakulteter is None:
        fakultet_clause = ""
    else:
        placeholders = ", ".join(["%s"] * len(fakulteter))
        fakultet_clause = f"AND KursPensumlisteView.fakultet IN ({placeholders})"
        params.extend(fakulteter)

    sql = SQL_BASE.format(
        aarsem_clause=aarsem_clause,
        pensumliste_clause=pensumliste_clause,
        fakultet_clause=fakultet_clause,
        variant_clause=variant_clause(variant),
    )
    return sql, tuple(params)
