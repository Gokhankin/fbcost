import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

print('=== PERSONEL MUTFAK EXITS IN SEDNA (SEP 2026) ===')
# Let's check all slips related to depot 029 or personel
c.execute("""
    SELECT 
        so.Type,
        so.DocumNo,
        so.ConsumptionDepot,
        COUNT(st.RecId),
        SUM(st.Amount)
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND (st.EntryingDepot = '029' OR so.ConsumptionDepot = '029')
    GROUP BY so.Type, so.DocumNo, so.ConsumptionDepot
""")
for r in c.fetchall():
    print(r)

# Check how Excel got 668,091.75 TL gross personel cost:
c.execute("""
    SELECT 
        COUNT(st.RecId),
        SUM(st.Amount)
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND st.EntryingDepot = '029'
""")
print('\nEntryingDepot 029 total across all types:', c.fetchone())

conn.close()
