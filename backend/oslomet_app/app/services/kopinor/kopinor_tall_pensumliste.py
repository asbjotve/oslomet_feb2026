from typing import Any, Dict, List

import aiomysql

from app.services.kopinor.kopinor_filters import map_variant
from app.services.kopinor.kopinor_sql import build_kopinor_tall_sql


async def fetch_kopinor_tall_for_pensumliste(
    cursor: aiomysql.DictCursor,
    *,
    aarsem: str,
    pensumliste_id: int,
    fakultet: str = "ALLE",
    variant: str = "ALLE",
) -> List[Dict[str, Any]]:
    v = map_variant(variant)
    sql, params = build_kopinor_tall_sql(
        aarsem=aarsem,
        fakultet=fakultet,
        variant=v,
        partial_aarsem=False,
        pensumliste_id=pensumliste_id,
    )

    await cursor.execute(sql, params)
    rows = await cursor.fetchall()
    return list(rows)
