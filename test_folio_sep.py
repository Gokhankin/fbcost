import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

c.execute('''
    SELECT 
        f.DepartCode,
        d.DepartName,
        COUNT(*),
        SUM(f.LocalAmount)
    FROM Folio f
    LEFT JOIN Department d ON d.DepartCode = f.DepartCode
    WHERE YEAR(f.PostDate) = 2026 AND MONTH(f.PostDate) = 9
    GROUP BY f.DepartCode, d.DepartName
    ORDER BY SUM(f.LocalAmount) DESC
''')
for r in c.fetchall():
    print(f"Depart: {str(r[0]):>5} | {str(r[1]):<30} | Rows: {r[2]:>5} | LocalAmount: {r[3]:>14,.2f} TL")

conn.close()
