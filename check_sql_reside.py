import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection, get_db_connection

print("=== 1. CHECKING PRODUCT GROUP TABLES IN ANTMARINSEDNA2021 ===")
conn_stk = get_stock_db_connection()
c_stk = conn_stk.cursor()
c_stk.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME LIKE '%Group%' OR TABLE_NAME LIKE '%Category%' OR TABLE_NAME LIKE '%Product%'
    ORDER BY TABLE_NAME
""")
for r in c_stk.fetchall():
    print("  Stock Table:", r[0])

print("\n=== 2. CHECKING PRODUCT TABLE GROUP COLUMNS ===")
c_stk.execute("""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Product' AND (COLUMN_NAME LIKE '%RecId%' OR COLUMN_NAME LIKE '%Group%' OR COLUMN_NAME LIKE '%Code%')
""")
for r in c_stk.fetchall():
    print(f"  Product Col: {r[0]} ({r[1]})")

conn_stk.close()

print("\n=== 3. CHECKING POS SUMMARY DEPARTMENTS & TYPES IN ADAKOY2026 ===")
conn_pms = get_db_connection()
c_pms = conn_pms.cursor()
c_pms.execute("""
    SELECT 
        ps.DepartCode,
        d.DepartName,
        SUM(ISNULL(ps.PriceTotal, 0)) AS TotalPrice,
        SUM(ISNULL(ps.NetAmount, 0)) AS NetTotal
    FROM PosSummary ps
    LEFT JOIN Department d ON d.DepartCode = ps.DepartCode
    WHERE YEAR(ps.SellingDate) = 2026 AND MONTH(ps.SellingDate) = 9
    GROUP BY ps.DepartCode, d.DepartName
    ORDER BY TotalPrice DESC
""")
for r in c_pms.fetchall():
    print(f"  POS Depart: {str(r[0]):>4} | {str(r[1]):<30} | Total: {r[2]:>14,.2f} TL | Net: {r[3]:>14,.2f} TL")

conn_pms.close()
