import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

try:
    c.execute("""
        SELECT TOP 5 so.RecId, so.Dates, so.Type, so.VoucherNo
        FROM StockOwner so
        WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
          AND so.Type = '29'
    """)
    for r in c.fetchall():
        print(r)
except Exception as e:
    print('Error:', e)

conn.close()
