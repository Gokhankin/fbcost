import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

print("Folio totals with PostDate for Sep 2026:")
c.execute('''
    SELECT 
        f.DepartCode,
        d.DepartName,
        COUNT(f.RecId),
        SUM(ISNULL(f.LocalAmount, 0))
    FROM Folio f
    LEFT JOIN Department d ON d.DepartCode = f.DepartCode
    WHERE f.PostDate >= '2026-09-01' AND f.PostDate <= '2026-09-30 23:59:59'
    GROUP BY f.DepartCode, d.DepartName
    ORDER BY SUM(ISNULL(f.LocalAmount, 0)) DESC
''')
for r in c.fetchall():
    print(f"  {str(r[0]):>5} | {str(r[1]):<30} | {r[2]:>5} | {r[3]:>14,.2f} TL")

conn.close()
