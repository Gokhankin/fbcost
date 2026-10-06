import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

print("=== Ara Grup (SubGroup) in Sep 2026 Type 29 ===")
c.execute("""
    SELECT 
        ISNULL(sg.Remark, 'Tanımsız') AS SubGroupName,
        COUNT(st.RecId) AS KalemCount,
        SUM(ISNULL(st.Amount, 0)) AS TotalAmount
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    JOIN Product p ON p.RecId = st.CardId
    LEFT JOIN SubGroup sg ON sg.RecId = p.SubRecId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = '29'
    GROUP BY sg.Remark
    ORDER BY TotalAmount DESC
""")
for r in c.fetchall()[:12]:
    print(f"  {str(r[0]):<35} | {r[1]:>4} Kalem | {r[2]:>14,.2f} TL")

print("\n=== Alt Grup (IntermediateGroup) in Sep 2026 Type 29 ===")
c.execute("""
    SELECT 
        ISNULL(ig.Remark, 'Tanımsız') AS InterGroupName,
        COUNT(st.RecId) AS KalemCount,
        SUM(ISNULL(st.Amount, 0)) AS TotalAmount
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    JOIN Product p ON p.RecId = st.CardId
    LEFT JOIN IntermediateGroup ig ON ig.RecId = p.IntermediateRecId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = '29'
    GROUP BY ig.Remark
    ORDER BY TotalAmount DESC
""")
for r in c.fetchall()[:12]:
    print(f"  {str(r[0]):<35} | {r[1]:>4} Kalem | {r[2]:>14,.2f} TL")

conn.close()
