import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

print('=== POS REVENUE IN SEPTEMBER 2026 ===')
c.execute("""
    SELECT 
        d.DepartCode,
        d.DepartName,
        SUM(ISNULL(ps.PriceTotal, 0)),
        SUM(ISNULL(ps.NetAmount, 0))
    FROM PosSummary ps
    JOIN Department d ON d.DepartCode = ps.DepartCode
    WHERE ps.SellingDate >= '2026-09-01' AND ps.SellingDate <= '2026-09-30 23:59:59'
    GROUP BY d.DepartCode, d.DepartName
    ORDER BY SUM(ISNULL(ps.PriceTotal, 0)) DESC
""")
for r in c.fetchall():
    print(f"  {r[0]:>3} | {r[1]:<30} | Total: {r[2]:>14,.2f} TL | Net: {r[3]:>14,.2f} TL")

conn.close()
