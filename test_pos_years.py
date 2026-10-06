import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

c.execute('''
    SELECT YEAR(SellingDate), COUNT(*)
    FROM PosSummary
    GROUP BY YEAR(SellingDate)
    ORDER BY YEAR(SellingDate)
''')
for r in c.fetchall():
    print(r)

conn.close()
