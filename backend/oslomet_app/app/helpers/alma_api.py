from __future__ import annotations

from typing import Optional
import aiomysql

async def get_url_list(pool, year):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            if year == "all":
                await cursor.execute("SELECT id, owner_url FROM api_alma_pensumlister")
            else:
                await cursor.execute(
                    "SELECT id, owner_url FROM api_alma_pensumlister WHERE course_year = %s", (year,)
                )
            rows = await cursor.fetchall()
    # Retur dict: {id: owner_url, ...}
    return {row['id']: row['owner_url'] for row in rows}

def normalize_years_input(year_input: str) -> list[Optional[str]]:
    """
    Normaliserer query-parametere som:
      - "all" -> [None]
      - "2024" -> ["2024"]
      - "2024, 2025" -> ["2024", "2025"]

    Return:
      list[str | None]
        None betyr "all" (altså ingen year-filter i Alma-query / DB-query avhengig av kontekst).
    """
    if year_input is None:
        raise ValueError("year_input kan ikke være None")

    raw = year_input.strip()
    if not raw:
        raise ValueError("year_input kan ikke være tom")

    if raw.lower() == "all":
        return [None]

    years = [p.strip() for p in raw.split(",") if p.strip()]
    if not years:
        raise ValueError("Fant ingen år i input")

    for y in years:
        if not y.isdigit():
            raise ValueError(f"Ugyldig år: {y}")

    return years
