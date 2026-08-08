import psycopg as sql,os
with sql.connect(dbname=os.getenv("db_name")) as con:
    pass