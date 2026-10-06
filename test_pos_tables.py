import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

print("=== CHECKING POS TABLES IN ADAKOY2026 ===")
c.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME LIKE '%Pos%' OR TABLE_NAME LIKE '%Department%' OR TABLE_NAME LIKE '%Revenue%'
    ORDER BY TABLE_NAME
""")
for r in c.fetchall():
    print(" ", r[0])

print("\n=== CHECKING TOTAL FOLIO EXTRA SALES IN SEP 2026 ===")
# Check Folio or DailyRevenue
c.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME LIKE '%Folio%' OR TABLE_NAME LIKE '%Daily%'
    ORDER BY TABLE_NAME
""")
for r in c.fetchall():
    print(" ", r[0])

conn.close()
