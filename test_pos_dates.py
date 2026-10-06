import sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_db_connection
conn = get_db_connection()
c = conn.cursor()
c.execute('SELECT MIN(SellingDate), MAX(SellingDate), COUNT(*) FROM PosSummary')
print('PosSummary dates:', c.fetchone())
conn.close()
