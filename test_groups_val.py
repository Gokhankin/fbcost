import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

conn = get_stock_db_connection()
c = conn.cursor()

print("=== MainGroup ===")
c.execute("SELECT RecId, MainCode, Remark FROM MainGroup")
for r in c.fetchall():
    print(f"  {r[0]:>3} | {r[1]:<10} | {r[2]}")

print("\n=== SubGroup (Sample 15) ===")
c.execute("SELECT TOP 15 RecId, MainRecId, SubCode, Remark FROM SubGroup")
for r in c.fetchall():
    print(f"  {r[0]:>3} | Main: {str(r[1]):>3} | {str(r[2]):<10} | {r[3]}")

print("\n=== IntermediateGroup (Sample 15) ===")
c.execute("SELECT TOP 15 RecId, MainRecId, SubRecId, IntermediateCode, Remark FROM IntermediateGroup")
for r in c.fetchall():
    print(f"  {r[0]:>3} | Main: {str(r[1]):>3} | Sub: {str(r[2]):>3} | {str(r[3]):<10} | {r[4]}")

conn.close()
