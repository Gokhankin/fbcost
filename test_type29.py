import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

print('=== INSPECT TYPE 29 SLIPS IN SEDNA SQL (SEPTEMBER 2026) ===')
c.execute("""
    SELECT 
        mg.Remark AS MainGroupName,
        COUNT(st.RecId) AS ItemCount,
        SUM(ISNULL(st.Amount, 0)) AS TotalAmount
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    JOIN Product p ON p.RecId = st.CardId
    LEFT JOIN MainGroup mg ON mg.GroupCode = SUBSTRING(p.ProductCode, 1, 2)
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = '29'
    GROUP BY mg.Remark
    ORDER BY TotalAmount DESC
""")
for r in c.fetchall():
    print(f"  Grup: {str(r[0]):<30} | Kalem: {r[1]:>5} | Tutar: {r[2]:>14,.2f} TL")

conn.close()
