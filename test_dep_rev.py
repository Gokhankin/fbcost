import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

print("=== DepartmentRevenue for Sep 2026 ===")
c.execute("""
    SELECT 
        d.DepartCode,
        d.DepartName,
        SUM(dr.Amount)
    FROM DepartmentRevenue dr
    JOIN Department d ON d.RecId = dr.DepartmentId
    WHERE dr.RevenueDate >= '2026-09-01' AND dr.RevenueDate <= '2026-09-30 23:59:59'
    GROUP BY d.DepartCode, d.DepartName
    ORDER BY SUM(dr.Amount) DESC
""")
for r in c.fetchall():
    print(f"  {r[0]:>5} | {str(r[1]):<35} | {r[2]:>14,.2f} TL")

conn.close()
