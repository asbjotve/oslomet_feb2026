import re
from typing import Optional, Dict, Any, Tuple

ALLOWED_COLUMNS = {
    "filnavn",
    "sideangivelse",
    "artikkel_tittel",
    "forfatter",
    "tidsskrift",
    "issn",
    "utgitt",
    "argang_volume",
    "hefte_issue",
    "merknad",
}

SELECT_COLUMNS = """
    filnavn,
    sideangivelse,
    artikkel_tittel,
    forfatter,
    tidsskrift,
    issn,
    utgitt,
    argang_volume,
    hefte_issue,
    merknad
"""


def _normalize_paging(page: int, page_size: int) -> Tuple[int, int, int]:
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    offset = (page - 1) * page_size
    return page, page_size, offset


def _normalize_sort(sort: Optional[str], direction: Optional[str]) -> Tuple[str, str]:
    sort_col = (sort or "artikkel_tittel").strip()
    if sort_col not in ALLOWED_COLUMNS:
        sort_col = "artikkel_tittel"

    sort_dir = (direction or "asc").strip().lower()
    if sort_dir not in ("asc", "desc"):
        sort_dir = "asc"

    return sort_col, sort_dir


def _validate_regex(pattern: str) -> None:
    if len(pattern) > 100:
        raise ValueError("Regex er for lang (maks 100 tegn).")
    re.compile(pattern)


async def get_artikler_data(
    cursor,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    column: Optional[str] = None,
    sort: Optional[str] = "artikkel_tittel",
    direction: Optional[str] = "asc",
    use_regex: bool = False,
) -> Dict[str, Any]:
    page, page_size, offset = _normalize_paging(page, page_size)
    sort_col, sort_dir = _normalize_sort(sort, direction)

    where_clauses = []
    params = []

    if search and search.strip():
        s = search.strip()
        requested_col = (column or "").strip()

        if use_regex:
            _validate_regex(s)

            if requested_col in ALLOWED_COLUMNS:
                where_clauses.append(f"`{requested_col}` REGEXP %s")
                params.append(s)
            else:
                where_clauses.append(
                    "("
                    "`filnavn` REGEXP %s OR "
                    "`sideangivelse` REGEXP %s OR "
                    "`artikkel_tittel` REGEXP %s OR "
                    "`forfatter` REGEXP %s OR "
                    "`tidsskrift` REGEXP %s OR "
                    "`issn` REGEXP %s OR "
                    "`utgitt` REGEXP %s OR "
                    "`argang_volume` REGEXP %s OR "
                    "`hefte_issue` REGEXP %s OR "
                    "`merknad` REGEXP %s"
                    ")"
                )
                params.extend([s, s, s, s, s, s, s, s, s, s])

        else:
            like = f"%{s}%"

            if requested_col in ALLOWED_COLUMNS:
                where_clauses.append(f"`{requested_col}` LIKE %s")
                params.append(like)
            else:
                where_clauses.append(
                    "("
                    "`filnavn` LIKE %s OR "
                    "`sideangivelse` LIKE %s OR "
                    "`artikkel_tittel` LIKE %s OR "
                    "`forfatter` LIKE %s OR "
                    "`tidsskrift` LIKE %s OR "
                    "`issn` LIKE %s OR "
                    "`utgitt` LIKE %s OR "
                    "`argang_volume` LIKE %s OR "
                    "`hefte_issue` LIKE %s OR "
                    "`merknad` LIKE %s"
                    ")"
                )
                params.extend([like, like, like, like, like, like, like, like, like, like])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM `db_oslomet`.`filoversikt_artikler`
        {where_sql}
    """
    await cursor.execute(count_sql, tuple(params))
    count_row = await cursor.fetchone()
    total = int(count_row["total"]) if count_row else 0

    data_sql = f"""
        SELECT {SELECT_COLUMNS}
        FROM `db_oslomet`.`filoversikt_artikler`
        {where_sql}
        ORDER BY `{sort_col}` {sort_dir.upper()}
        LIMIT %s OFFSET %s
    """
    data_params = params + [page_size, offset]
    await cursor.execute(data_sql, tuple(data_params))
    rows = await cursor.fetchall()

    data = [{"fieldData": row} for row in rows]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "data": data,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": total_pages,
        },
        "sorting": {
            "sort": sort_col,
            "direction": sort_dir,
        },
        "filter": {
            "search": search or "",
            "column": column or "",
            "use_regex": use_regex,
        },
    }
