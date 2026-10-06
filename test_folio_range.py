import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection

conn = get_db_connection()
c = conn.cursor()

c.execute("SELECT MIN(PostDate), MAX(PostDate), COUNT(*) FROM Folio")
print("Folio PostDate:", c.fetchone())

c.execute("SELECT MIN(CurrDate), MAX(CurrDate), COUNT(*) FROM Folio")
print("Folio CurrDate:", c.fetchone())

c.execute("SELECT TOP 5 PostDate, CurrDate, DepartCode, Amount, LocalAmount FROM Folio ORDER BY RecId DESC")
for r in c.fetchall():
    print("  ", r)

conn.close()
