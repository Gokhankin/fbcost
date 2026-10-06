import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

c.execute('''
    SELECT 
        ps.DepartCode,
        d.DepartName,
        COUNT(*),
        SUM(ps.PriceTotal),
        SUM(ps.NetAmount)
    FROM PosSummary ps
    LEFT JOIN Department d ON d.DepartCode = ps.DepartCode
    WHERE YEAR(ps.SellingDate) = 2026 AND MONTH(ps.SellingDate) = 9
    GROUP BY ps.DepartCode, d.DepartName
    ORDER BY SUM(ps.PriceTotal) DESC
''')
for r in c.fetchall():
    print(f"Depart: {str(r[0]):>5} | {str(r[1]):<30} | Rows: {r[2]:>5} | Gross: {r[3]:>14,.2f} TL | Net: {r[4]:>14,.2f} TL")

conn.close()
