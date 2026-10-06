import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

for tbl in ['MainGroup', 'IntermediateGroup', 'SubGroup']:
    print(f"\nColumns of {tbl}:")
    c.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tbl}'")
    for r in c.fetchall():
        print(f"  {r[0]} ({r[1]})")

conn.close()
