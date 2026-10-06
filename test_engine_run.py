import os, sys, json
sys.path.append('/home/society/Masaüstü/fbcost')
from app import get_stock_db_connection

def test_fetch_stock(start_str, end_str, mode='monthly'):
    conn = get_stock_db_connection()
    if not conn:
        print("Could not connect to Stock DB")
        return
        
    c = conn.cursor()
    
    # 1. Detect slip type
    c.execute("""
        SELECT COUNT(*)
        FROM StockTrans st
        JOIN StockOwner so ON so.RecId = st.StockOwnerId
        WHERE so.Dates >= CONVERT(DATETIME, ?, 120) 
          AND so.Dates <= CONVERT(DATETIME, ?, 120)
          AND so.Type = '29'
    """, (start_str, end_str))
    cnt29 = c.fetchone()[0] or 0
    slip_type = '29' if (mode == 'monthly' and cnt29 > 0) else '20'
    print(f"Target Slip Type: {slip_type} (Count 29 rows: {cnt29})")
    
    # 2. Category totals
    q_cats = """
        SELECT 
            CASE 
                WHEN p.ProductCode LIKE '01%' THEN 'Food'
                WHEN p.ProductCode LIKE '0201%' THEN 'Alcohol'
                WHEN (p.ProductCode LIKE '0202%' OR p.ProductCode LIKE '0203%') THEN 'Soft_Beverage'
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
        WHERE so.Dates >= CONVERT(DATETIME, ?, 120) 
          AND so.Dates <= CONVERT(DATETIME, ?, 120)
          AND so.Type = ?
        GROUP BY 
            CASE 
                WHEN p.ProductCode LIKE '01%' THEN 'Food'
                WHEN p.ProductCode LIKE '0201%' THEN 'Alcohol'
                WHEN (p.ProductCode LIKE '0202%' OR p.ProductCode LIKE '0203%') THEN 'Soft_Beverage'
                WHEN p.ProductCode LIKE '03%' THEN 'Cleaning'
                WHEN p.ProductCode LIKE '05%' THEN 'Operational'
                WHEN p.ProductCode LIKE '06%' THEN 'Fuel'
                WHEN p.ProductCode LIKE '12%' THEN 'Market'
                ELSE 'Other'
            END
    """
    c.execute(q_cats, (start_str, end_str, slip_type))
    cat_dict = {}
    for r in c.fetchall():
        cat_dict[r[0]] = {"count": r[1], "amount": float(r[2] or 0)}
        
    food_total = cat_dict.get('Food', {}).get('amount', 0.0)
    alc_total = cat_dict.get('Alcohol', {}).get('amount', 0.0)
    soft_total = cat_dict.get('Soft_Beverage', {}).get('amount', 0.0)
    bev_total = alc_total + soft_total
    
    # 3. Staff Canteen
    q_staff = """
        SELECT 
            CASE 
                WHEN p.ProductCode LIKE '01%' THEN 'Staff_Food'
                ELSE 'Staff_Bev'
            END AS StaffCategory,
            COUNT(st.RecId) AS ItemCount,
            SUM(ISNULL(st.Amount, 0)) AS TotalAmount
        FROM StockTrans st
        JOIN StockOwner so ON so.RecId = st.StockOwnerId
        JOIN Product p ON p.RecId = st.CardId
        WHERE so.Dates >= CONVERT(DATETIME, ?, 120) 
          AND so.Dates <= CONVERT(DATETIME, ?, 120)
          AND so.Type = ?
          AND (ISNULL(NULLIF(so.ConsumptionDepot, ''), st.EntryingDepot) = '029')
        GROUP BY 
            CASE 
                WHEN p.ProductCode LIKE '01%' THEN 'Staff_Food'
                ELSE 'Staff_Bev'
            END
    """
    c.execute(q_staff, (start_str, end_str, slip_type))
    staff_dict = {}
    for r in c.fetchall():
        staff_dict[r[0]] = float(r[2] or 0)
        
    staff_food = staff_dict.get('Staff_Food', 0.0)
    staff_bev = staff_dict.get('Staff_Bev', 0.0)
    staff_total = staff_food + staff_bev
    
    # 4. Top 10 items
    q_top10 = """
        SELECT TOP 10
            p.ProductCode,
            p.Remark AS ProductName,
            p.Unit,
            SUM(ISNULL(st.Quantity, 0)) AS TotalQty,
            SUM(ISNULL(st.Amount, 0)) AS TotalAmount
        FROM StockTrans st
        JOIN StockOwner so ON so.RecId = st.StockOwnerId
        JOIN Product p ON p.RecId = st.CardId
        WHERE so.Dates >= CONVERT(DATETIME, ?, 120) 
          AND so.Dates <= CONVERT(DATETIME, ?, 120)
          AND so.Type = ?
        GROUP BY p.ProductCode, p.Remark, p.Unit
        ORDER BY TotalAmount DESC
    """
    c.execute(q_top10, (start_str, end_str, slip_type))
    top10 = []
    for r in c.fetchall():
        top10.append({
            "code": str(r[0] or '').strip(),
            "name": str(r[1] or '').strip(),
            "unit": str(r[2] or '').strip(),
            "qty": float(r[3] or 0),
            "amount": float(r[4] or 0)
        })
        
    # 5. Depot Breakdown
    depot_names = {
        "002": "Ana Mutfak", "003": "Ana Bar", "004": "Beach Bar",
        "005": "Pool Bar", "006": "Captain Cook Bar", "017": "A la Carte Bar",
        "018": "Night Bar", "021": "Pastane", "024": "Soğuk Mutfak",
        "026": "Kasaphane", "028": "Bulaşıkhane", "029": "Personel Yemekhane"
    }
    q_depots = """
        SELECT 
            ISNULL(NULLIF(so.ConsumptionDepot, ''), st.EntryingDepot) AS DepotCode,
            SUM(ISNULL(st.Amount, 0)) AS TotalAmount
        FROM StockTrans st
        JOIN StockOwner so ON so.RecId = st.StockOwnerId
        WHERE so.Dates >= CONVERT(DATETIME, ?, 120) 
          AND so.Dates <= CONVERT(DATETIME, ?, 120)
          AND so.Type = ?
        GROUP BY ISNULL(NULLIF(so.ConsumptionDepot, ''), st.EntryingDepot)
        ORDER BY TotalAmount DESC
    """
    c.execute(q_depots, (start_str, end_str, slip_type))
    depots = []
    for r in c.fetchall():
        dcode = str(r[0] or '').strip()
        amt = float(r[1] or 0)
        if amt > 0:
            depots.append({
                "code": dcode,
                "name": depot_names.get(dcode, f"Depo {dcode}"),
                "amount": amt
            })
            
    conn.close()
    
    print("RESULTS:")
    print(f"  Food: {food_total:,.2f} TL")
    print(f"  Alcohol: {alc_total:,.2f} TL")
    print(f"  Soft Bev: {soft_total:,.2f} TL")
    print(f"  Total F&B: {food_total + alc_total + soft_total:,.2f} TL")
    print(f"  Staff Gross: {staff_total:,.2f} TL (Food: {staff_food:,.2f}, Bev: {staff_bev:,.2f})")
    print(f"  Depots count: {len(depots)}")
    print(f"  Top 10 count: {len(top10)}")

test_fetch_stock('2026-09-01 00:00:00', '2026-09-30 23:59:59', mode='monthly')
