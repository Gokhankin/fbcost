import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

c.execute("""
    SELECT TOP 10 so.RecId, so.Dates, so.Type, so.VoucherNo, so.Remark, COUNT(st.RecId), SUM(st.Amount)
    FROM StockOwner so
    LEFT JOIN StockTrans st ON st.StockOwnerId = so.RecId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = 29
    GROUP BY so.RecId, so.Dates, so.Type, so.VoucherNo, so.Remark
""")
for r in c.fetchall():
    print(r)

conn.close()
