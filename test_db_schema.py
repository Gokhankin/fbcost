import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection, get_db_connection

conn_stk = get_stock_db_connection()
if conn_stk:
    print('CONNECTED TO STOCK DB (ANTMARINSEDNA2021)!')
    c = conn_stk.cursor()
    c.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Cost%' OR TABLE_NAME LIKE '%Stock%' OR TABLE_NAME LIKE '%Count%' OR TABLE_NAME LIKE '%Depot%' OR TABLE_NAME LIKE '%Product%' OR TABLE_NAME LIKE '%Recipe%' OR TABLE_NAME LIKE '%Group%' ORDER BY TABLE_NAME")
    for r in c.fetchall():
        print('  STOCK DB TABLE:', r[0])
    conn_stk.close()
else:
    print('Failed to connect to stock DB')

conn_pms = get_db_connection()
if conn_pms:
    print('\nCONNECTED TO PMS DB (Adakoy2026)!')
    c = conn_pms.cursor()
    c.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%Cost%' OR TABLE_NAME LIKE '%Pos%' OR TABLE_NAME LIKE '%Stay%' OR TABLE_NAME LIKE '%Folio%' ORDER BY TABLE_NAME")
    for r in c.fetchall():
        print('  PMS DB TABLE:', r[0])
    conn_pms.close()
