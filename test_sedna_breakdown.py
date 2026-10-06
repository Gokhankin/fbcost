import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection, get_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

print('=== STOCK SLIP TYPES IN SEPTEMBER 2026 ===')
c.execute("""
    SELECT so.Type, COUNT(*), SUM(ISNULL(st.Amount, 0))
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
    GROUP BY so.Type
    ORDER BY SUM(ISNULL(st.Amount, 0)) DESC
""")
for r in c.fetchall():
    print(f"  Type: {r[0]:>3} | Count: {r[1]:>5} | Sum Amount: {r[2]:>14,.2f} TL")

print('\n=== DEPOT AMOUNTS IN SEPTEMBER 2026 (TRANSFER TYPE 20) ===')
c.execute("""
    SELECT st.EntryingDepot, COUNT(*), SUM(ISNULL(st.Amount, 0))
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = '20'
    GROUP BY st.EntryingDepot
    ORDER BY SUM(ISNULL(st.Amount, 0)) DESC
""")
for r in c.fetchall():
    print(f"  Depot: {str(r[0]):>5} | Count: {r[1]:>5} | Amount: {r[2]:>14,.2f} TL")

conn.close()
