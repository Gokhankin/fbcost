import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

print("Sample rows in PosSummary in Sep 2026:")
c.execute('''
    SELECT TOP 5 ps.SellingDate, ps.DepartCode, ps.PriceTotal, ps.NetAmount
    FROM PosSummary ps
    WHERE ps.SellingDate >= '2026-09-01' AND ps.SellingDate <= '2026-09-30 23:59:59'
''')
for r in c.fetchall():
    print(r)

print("\nDistinct DepartCode in Sep 2026:")
c.execute('''
    SELECT ps.DepartCode, COUNT(*), SUM(ps.PriceTotal)
    FROM PosSummary ps
    WHERE ps.SellingDate >= '2026-09-01' AND ps.SellingDate <= '2026-09-30 23:59:59'
    GROUP BY ps.DepartCode
''')
for r in c.fetchall():
    print(r)

conn.close()
