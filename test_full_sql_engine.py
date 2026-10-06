import os, sys
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection, get_db_connection

def test_full_sql_engine(year=2026, month=9):
    conn_stock = get_stock_db_connection()
    c_stk = conn_stock.cursor()
    
    start_date = f"{year:04d}-{month:02d}-01 00:00:00"
    end_date = f"{year:04d}-{month:02d}-30 23:59:59"
    
    print(f"=== TESTING SEDNA SQL ENGINE FOR {year}-{month:02d} ===")
    
    # 1. Check if Type 29 exists (Official Month-End Count)
    c_stk.execute("""
        SELECT COUNT(*), SUM(ISNULL(st.Amount, 0))
        FROM StockTrans st
        JOIN StockOwner so ON so.RecId = st.StockOwnerId
        WHERE so.Dates >= ? AND so.Dates <= ? AND so.Type = '29'
    """, (start_date, end_date))
    t29_cnt, t29_sum = c_stk.fetchone()
    print(f"Type 29 Count Slips: {t29_cnt} rows, Total: {t29_sum:,.2f} TL")
    
    slip_type = '29' if (t29_cnt and t29_cnt > 0) else '20'
    print(f"Using Slip Type: {slip_type}")
    
    # 2. Consumption by Main Prefix
    c_stk.execute("""
        SELECT 
            CASE 
                WHEN p.ProductCode LIKE '01%' THEN 'Food'
                WHEN p.ProductCode LIKE '0201%' THEN 'Alcohol'
                WHEN p.ProductCode LIKE '0202%' OR p.ProductCode LIKE '0203%' THEN 'Soft_Beverage'
                WHEN p.ProductCode LIKE '03%' THEN 'Cleaning'
                WHEN p.ProductCode LIKE '05%' THEN 'Operational'
                WHEN p.ProductCode LIKE '06%' THEN 'Fuel'
                WHEN p.ProductCode LIKE '12%' THEN 'Market'
                ELSE 'Other'
            END AS Category,
            COUNT(st.RecId) AS ItemCount,
            SUM(ISNULL(st.Amount, 0)) AS TotalAmount
        FROM StockTrans st
        JOIN StockOwner so ON so.RecId = st.StockOwnerId
        JOIN Product p ON p.RecId = st.CardId
        WHERE so.Dates >= ? AND so.Dates <= ? AND so.Type = ?
        GROUP BY 
            CASE 
                WHEN p.ProductCode LIKE '01%' THEN 'Food'
                WHEN p.ProductCode LIKE '0201%' THEN 'Alcohol'
                WHEN p.ProductCode LIKE '0202%' OR p.ProductCode LIKE '0203%' THEN 'Soft_Beverage'
                WHEN p.ProductCode LIKE '03%' THEN 'Cleaning'
                WHEN p.ProductCode LIKE '05%' THEN 'Operational'
                WHEN p.ProductCode LIKE '06%' THEN 'Fuel'
                WHEN p.ProductCode LIKE '12%' THEN 'Market'
                ELSE 'Other'
            END
    """, (start_date, end_date, slip_type))
    
    cats = {}
    for cat, cnt, amt in c_stk.fetchall():
        cats[cat] = {"count": cnt, "amount": float(amt or 0)}
        print(f"  {cat:<15}: {cnt:>5} items | {amt:>14,.2f} TL")
        
    food_total = cats.get('Food', {}).get('amount', 0.0)
    alc_total = cats.get('Alcohol', {}).get('amount', 0.0)
    soft_total = cats.get('Soft_Beverage', {}).get('amount', 0.0)
    bev_total = alc_total + soft_total
    total_fb = food_total + bev_total
    print(f"--> Total F&B Consumption: {total_fb:,.2f} TL (Food: {food_total:,.2f}, Bev: {bev_total:,.2f})")
    
    # 3. Staff Canteen
    c_stk.execute("""
        SELECT 
            COUNT(st.RecId),
            SUM(ISNULL(st.Amount, 0))
        FROM StockTrans st
        JOIN StockOwner so ON so.RecId = st.StockOwnerId
        WHERE so.Dates >= ? AND so.Dates <= ? 
          AND so.Type = ?
          AND (st.EntryingDepot = '029' OR so.ConsumptionDepot = '029')
    """, (start_date, end_date, slip_type))
    staff_cnt, staff_gross = c_stk.fetchone()
    staff_gross = float(staff_gross or 0)
    print(f"--> Staff Canteen Gross: {staff_cnt} items | {staff_gross:,.2f} TL")
    
    # Staff breakdown by Food vs Beverage
    c_stk.execute("""
        SELECT 
            CASE 
                WHEN p.ProductCode LIKE '01%' THEN 'Food'
                ELSE 'Beverage'
            END,
            SUM(ISNULL(st.Amount, 0))
        FROM StockTrans st
        JOIN StockOwner so ON so.RecId = st.StockOwnerId
        JOIN Product p ON p.RecId = st.CardId
        WHERE so.Dates >= ? AND so.Dates <= ? 
          AND so.Type = ?
          AND (st.EntryingDepot = '029' OR so.ConsumptionDepot = '029')
        GROUP BY 
            CASE 
                WHEN p.ProductCode LIKE '01%' THEN 'Food'
                ELSE 'Beverage'
            END
    """, (start_date, end_date, slip_type))
    staff_cats = {r[0]: float(r[1] or 0) for r in c_stk.fetchall()}
    print(f"    Staff Food: {staff_cats.get('Food', 0):,.2f} TL | Staff Bev: {staff_cats.get('Beverage', 0):,.2f} TL")
    
    conn_stock.close()
    
    # 4. PMS DB: Overnights and Rates
    conn_pms = get_db_connection()
    c_pms = conn_pms.cursor()
    iso_start = f"{year:04d}{month:02d}01"
    iso_end = f"{year:04d}{month:02d}30"
    
    c_pms.execute("""
        SELECT AVG(ISNULL(NULLIF(Invoice, 0), ISNULL(NULLIF(Pos, 0), Buying)))
        FROM ExchangeRate
        WHERE CurrencyCode = 'EUR'
          AND CurrDate >= CONVERT(DATETIME, ?, 112)
          AND CurrDate <= CONVERT(DATETIME, ?, 112) + ' 23:59:59'
    """, (iso_start, iso_end))
    eur_rate = float(c_pms.fetchone()[0] or 55.9092)
    print(f"--> EUR Rate: {eur_rate:.4f} TL")
    
    conn_pms.close()

test_full_sql_engine(2026, 9)
