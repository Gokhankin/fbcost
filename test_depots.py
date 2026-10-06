import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

print("=== CHECKING DEPOTS FOR TYPE 29 (COUNT) IN SEP 2026 ===")
c.execute('''
    SELECT 
        so.ConsumptionDepot,
        st.EntryingDepot,
        COUNT(*),
        SUM(st.Amount)
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = '29'
    GROUP BY so.ConsumptionDepot, st.EntryingDepot
    ORDER BY SUM(st.Amount) DESC
''')
for r in c.fetchall():
    print(r)

print("\n=== CHECKING DEPOTS FOR TYPE 20 (TRANSFERS) IN SEP 2026 ===")
c.execute('''
    SELECT 
        st.EntryingDepot,
        COUNT(*),
        SUM(st.Amount)
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = '20'
    GROUP BY st.EntryingDepot
    ORDER BY SUM(st.Amount) DESC
''')
for r in c.fetchall():
    print(r)

conn.close()
