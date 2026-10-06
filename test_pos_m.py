import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

c.execute('''
    SELECT MONTH(SellingDate), COUNT(*), MIN(SellingDate), MAX(SellingDate)
    FROM PosSummary
    WHERE YEAR(SellingDate) = 2026
    GROUP BY MONTH(SellingDate)
    ORDER BY MONTH(SellingDate)
''')
for r in c.fetchall():
    print(r)

conn.close()
