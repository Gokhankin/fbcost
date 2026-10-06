import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

c.execute("SELECT TOP 5 RecId, Dates, Type, DocumNo, ConsumptionType, ConsumptionDepot, Amount FROM StockOwner WHERE Dates >= '2026-09-01' AND Dates <= '2026-09-30' AND Type = '29'")
for r in c.fetchall():
    print(r)

print('\nTotal amount for Type 29 in Sep 2026:')
c.execute("""
    SELECT COUNT(*), SUM(st.Amount)
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = '29'
""")
print(c.fetchone())

conn.close()
