import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

print("=== MainGroup Sample ===")
c.execute("SELECT TOP 5 RecId, Code, Descriptions FROM MainGroup")
for r in c.fetchall():
    print(" ", r)

print("\n=== IntermediateGroup (Ara Grup) Sample ===")
c.execute("SELECT TOP 10 RecId, Code, Descriptions FROM IntermediateGroup")
for r in c.fetchall():
    print(" ", r)

print("\n=== SubGroup (Alt Grup) Sample ===")
c.execute("SELECT TOP 10 RecId, Code, Descriptions FROM SubGroup")
for r in c.fetchall():
    print(" ", r)

print("\n=== Testing Ara Grup Join with StockTrans in Sep 2026 ===")
c.execute("""
    SELECT 
        ig.Descriptions AS AraGrupName,
        COUNT(st.RecId) AS KalemSayisi,
        SUM(ISNULL(st.Amount, 0)) AS Tutar
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    JOIN Product p ON p.RecId = st.CardId
    LEFT JOIN IntermediateGroup ig ON ig.RecId = p.IntermediateRecId
    WHERE so.Dates >= '2026-09-01' AND so.Dates <= '2026-09-30 23:59:59'
      AND so.Type = '29'
    GROUP BY ig.Descriptions
    ORDER BY Tutar DESC
""")
for r in c.fetchall()[:10]:
    print(f"  {str(r[0]):<35} | {r[1]:>5} Kalem | {r[2]:>14,.2f} TL")

conn.close()
