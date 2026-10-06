import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection, get_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

print('=== PRODUCT PREFIXES & AMOUNTS FOR TYPE 29 (SEP 2026) ===')
c.execute("""
    SELECT 
        SUBSTRING(p.ProductCode, 1, 2) AS MainPrefix,
        COUNT(st.RecId) AS Cnt,
        SUM(ISNULL(st.Amount, 0)) AS TotalAmount
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    JOIN Product p ON p.RecId = st.CardId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = '29'
    GROUP BY SUBSTRING(p.ProductCode, 1, 2)
    ORDER BY TotalAmount DESC
""")
for r in c.fetchall():
    print(f"  Prefix: {str(r[0]):<6} | Kalem: {r[1]:>5} | Tutar: {r[2]:>14,.2f} TL")

print('\n=== PREFIX 02 (İÇECEKLER) SUB-PREFIXES ===')
c.execute("""
    SELECT 
        SUBSTRING(p.ProductCode, 1, 4) AS SubPrefix,
        COUNT(st.RecId) AS Cnt,
        SUM(ISNULL(st.Amount, 0)) AS TotalAmount
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    JOIN Product p ON p.RecId = st.CardId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = '29'
      AND p.ProductCode LIKE '02%'
    GROUP BY SUBSTRING(p.ProductCode, 1, 4)
    ORDER BY TotalAmount DESC
""")
for r in c.fetchall():
    print(f"  SubPrefix: {str(r[0]):<8} | Kalem: {r[1]:>5} | Tutar: {r[2]:>14,.2f} TL")

conn.close()
