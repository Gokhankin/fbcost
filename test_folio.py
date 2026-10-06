import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

print("Columns of Folio:")
c.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Folio'")
cols = [r[0] for r in c.fetchall()]
print(cols[:15])

print("\nFolio totals for Sep 2026:")
c.execute('''
    SELECT 
        d.DepartCode,
        d.DepartName,
        COUNT(f.RecId),
        SUM(ISNULL(f.PriceTotal, 0))
    FROM Folio f
    JOIN Department d ON d.RecId = f.DepartmentId
    WHERE f.TransDate >= '2026-09-01' AND f.TransDate <= '2026-09-30 23:59:59'
    GROUP BY d.DepartCode, d.DepartName
    ORDER BY SUM(ISNULL(f.PriceTotal, 0)) DESC
''')
for r in c.fetchall()[:10]:
    print(f"  {r[0]:>5} | {str(r[1]):<30} | {r[2]:>5} | {r[3]:>14,.2f} TL")

conn.close()
