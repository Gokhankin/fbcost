import sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection
conn = get_stock_db_connection()
c = conn.cursor()
c.execute('''
    SELECT 
        YEAR(so.Dates) as Yr,
        MONTH(so.Dates) as Mth,
        so.Type,
        COUNT(st.RecId) as Cnt,
        SUM(ISNULL(st.Amount, 0)) as TotalAmt
    FROM StockTrans st
    JOIN StockOwner so ON so.RecId = st.StockOwnerId
    WHERE YEAR(so.Dates) = 2026
    GROUP BY YEAR(so.Dates), MONTH(so.Dates), so.Type
    ORDER BY Yr, Mth, so.Type
''')
for r in c.fetchall():
    print(f"{r[0]}-{r[1]:02d} | Type: {r[2]} | Rows: {r[3]:>5} | Amt: {r[4]:>14,.2f} TL")
conn.close()
