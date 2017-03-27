from fabric.api import task

import asyncpg
import asyncio


async def init(user, password, database, host, port):
    # conn = await asyncpg.connect(user='postgres', password='wothing', database='butler',
    #                              host='127.0.0.1', port='5432')



    # await conn.execute(open(sql).read())
    # await conn.close()
    # return conn
    pass


@task
async def report_weekly(user, password, database, host, port):
    conn = await asyncpg.connect(user=user, password=password, database=database,
                    host=host, port=port)
    await conn.execute('SELECT * FROM ')
    conn.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(init())
