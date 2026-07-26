import psycopg2

conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='postgres',
    host='localhost',
    port='5432'
)
conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT 1 FROM pg_database WHERE datname='hris_db'")
if not cur.fetchone():
    cur.execute('CREATE DATABASE hris_db')
    print('Database hris_db created successfully!')
else:
    print('Database hris_db already exists.')

conn.close()
