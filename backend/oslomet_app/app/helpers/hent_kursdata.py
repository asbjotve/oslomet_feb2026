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
