import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

print("=== CHECKING POS DEPARTMENTS AND TOTALS FOR SEP 2026 ===")
c.execute("""
    SELECT 
        d.DepartCode,
        d.DepartName,
        SUM(ISNULL(ps.PriceTotal, 0)) AS GrossTotal,
        SUM(ISNULL(ps.NetAmount, 0)) AS NetTotal
    FROM PosSummary ps
    JOIN Department d ON d.DepartCode = ps.DepartCode
    WHERE ps.SellingDate >= '2026-09-01' AND ps.SellingDate <= '2026-09-30 23:59:59'
    GROUP BY d.DepartCode, d.DepartName
    ORDER BY GrossTotal DESC
""")
for r in c.fetchall():
    print(f"  Depart: {r[0]:>3} | {r[1]:<35} | Gross: {r[2]:>14,.2f} TL | Net: {r[3]:>14,.2f} TL")

conn.close()
