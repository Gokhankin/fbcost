from dotenv import load_dotenv
import os
import json
import calendar
import pyodbc
from datetime import datetime
from flask import Flask, render_template, jsonify, request

env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

app = Flask(__name__)

MONTHS_DATA_PATH = os.path.join(os.path.dirname(__file__), "fbcost_months_data.json")
DATA_PATH = os.path.join(os.path.dirname(__file__), "fbcost_data.json")

def load_all_months_data():
    if os.path.exists(MONTHS_DATA_PATH):
        try:
            with open(MONTHS_DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {MONTHS_DATA_PATH}: {e}")
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
                return {"2026-09": d}
        except Exception as e:
            print(f"Error loading {DATA_PATH}: {e}")
    return {}

def get_db_connection():
    db_srv = os.getenv("DB_SERVER", "192.168.0.41,1433")
    db_name = os.getenv("DB_NAME", "SednaAdakoy")
    db_usr = os.getenv("DB_USER", "gokhan")
    db_pwd = os.getenv("DB_PASS", "Ad!!2025!!")
    conn_str = os.getenv("DB_CONNECTION_STRING") or os.getenv("CONN_STR") or f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={db_srv};DATABASE={db_name};UID={db_usr};PWD={db_pwd};TrustServerCertificate=yes;"
    try:
        conn = pyodbc.connect(conn_str, timeout=3)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def get_stock_db_connection():
    conn_str = os.getenv("STOCK_DB_CONNECTION_STRING")
    if conn_str:
        try:
            return pyodbc.connect(conn_str, timeout=3)
        except Exception:
            pass

    stk_srv = os.getenv("STOCK_DB_SERVER", "10.0.0.11")
    stk_port = os.getenv("STOCK_DB_PORT", "1433")
    stk_db = os.getenv("STOCK_DB_NAME", "ANTMARINSEDNA2021")
    stk_usr = os.getenv("STOCK_DB_USER", "sa")
    stk_pwd = os.getenv("STOCK_DB_PASS", "00-0C-29-35-5A-D3")

    freetds_str = f"DRIVER=FreeTDS;SERVER={stk_srv};PORT={stk_port};DATABASE={stk_db};UID={stk_usr};PWD={stk_pwd};TDS_Version=7.4;"
    try:
        return pyodbc.connect(freetds_str, timeout=3)
    except Exception:
        pass

    ms_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={stk_srv},{stk_port};DATABASE={stk_db};UID={stk_usr};PWD={stk_pwd};TrustServerCertificate=yes;"
    try:
        return pyodbc.connect(ms_str, timeout=3)
    except Exception as e:
        print(f"Stock DB connection error: {e}")
        return None

def fetch_live_stock_data(start_str, end_str):
    conn = get_stock_db_connection()
    if not conn:
        return {
            "fb_totals": {"food": 0.0, "beverage": 0.0, "alcohol": 0.0, "staff": 0.0, "staff_food": 0.0, "staff_bev": 0.0, "staff_alc": 0.0, "total": 0.0},
            "detayli_stok": [],
            "personel_stok": [],
            "fb_analytics": {"top10_items": [], "depot_breakdown": [], "zayi_items": [], "total_zayi_amount": 0.0}
        }

    stock_payload = {}
    try:
        cursor = conn.cursor()
        
        # 1. Total F&B Consumption breakdown by category/depot from Sedna SQL
        q_categories = """
            SELECT 
                st.EntryingDepot,
                p.MainRecId,
                SUM(ISNULL(st.Amount, 0)) AS TotalAmount
            FROM StockTrans st
            JOIN StockOwner so ON so.RecId = st.StockOwnerId
            LEFT JOIN Product p ON p.RecId = st.CardId
            WHERE so.Dates >= CONVERT(DATETIME, ?, 120) 
              AND so.Dates <= CONVERT(DATETIME, ?, 120)
              AND so.Type = '20'
            GROUP BY st.EntryingDepot, p.MainRecId
        """
        cursor.execute(q_categories, (start_str, end_str))
        cat_rows = cursor.fetchall()

        food_total = 0.0
        bev_total = 0.0
        alc_total = 0.0
        staff_total = 0.0

        staff_food = 0.0
        staff_bev = 0.0
        staff_alc = 0.0

        for r in cat_rows:
            depot = (r[0] or '').strip()
            main_cat = r[1]
            amt = float(r[2] or 0)

            if depot == '029':
                staff_total += amt
                if main_cat == 3:
                    staff_alc += amt
                elif main_cat == 2:
                    staff_bev += amt
                else:
                    staff_food += amt
            elif main_cat == 3: # Alcohol category across all bar depots
                alc_total += amt
            elif main_cat == 2: # Beverage category across all bar depots
                bev_total += amt
            else: # Food / General warehouse exits
                food_total += amt

        stock_payload["fb_totals"] = {
            "food": food_total,
            "beverage": bev_total,
            "alcohol": alc_total,
            "staff": staff_total,
            "staff_food": staff_food,
            "staff_bev": staff_bev,
            "staff_alc": staff_alc,
            "total": food_total + bev_total + alc_total + staff_total
        }

        # 2. Detailed Stock Exits (Detaylı Stok Tüketimi)
        q_detay = """
            SELECT 
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
              AND so.Type = '20'
            GROUP BY p.ProductCode, p.Remark, p.Unit
            ORDER BY TotalAmount DESC
        """
        cursor.execute(q_detay, (start_str, end_str))
        detay_rows = cursor.fetchall()
        stock_payload["detayli_stok"] = [
            {
                "code": str(r[0] or '').strip(),
                "name": str(r[1] or '').strip(),
                "unit": str(r[2] or '').strip(),
                "qty": float(r[3] or 0),
                "amount": float(r[4] or 0)
            } for r in detay_rows
        ]

        # 3. Staff Canteen Items (Personel Yemekhane - Depot 029)
        q_staff = """
            SELECT 
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
              AND so.Type = '20'
              AND st.EntryingDepot = '029'
            GROUP BY p.ProductCode, p.Remark, p.Unit
            ORDER BY TotalAmount DESC
        """
        cursor.execute(q_staff, (start_str, end_str))
        staff_rows = cursor.fetchall()
        stock_payload["personel_stok"] = [
            {
                "code": str(r[0] or '').strip(),
                "name": str(r[1] or '').strip(),
                "unit": str(r[2] or '').strip(),
                "qty": float(r[3] or 0),
                "amount": float(r[4] or 0)
            } for r in staff_rows
        ]

        # 4. F&B Manager Executive Analytics (Top 10, Depot Breakdown, Zayi/Scrap Type 25)
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
              AND so.Type = '20'
            GROUP BY p.ProductCode, p.Remark, p.Unit
            ORDER BY TotalAmount DESC
        """
        cursor.execute(q_top10, (start_str, end_str))
        top10_items = [
            {
                "code": str(r[0] or '').strip(),
                "name": str(r[1] or '').strip(),
                "unit": str(r[2] or '').strip(),
                "qty": float(r[3] or 0),
                "amount": float(r[4] or 0)
            } for r in cursor.fetchall()
        ]

        # 4b. Depot Outlet Breakdown
        q_depot = """
            SELECT 
                st.EntryingDepot,
                SUM(ISNULL(st.Amount, 0)) AS TotalAmount
            FROM StockTrans st
            JOIN StockOwner so ON so.RecId = st.StockOwnerId
            WHERE so.Dates >= CONVERT(DATETIME, ?, 120)
              AND so.Dates <= CONVERT(DATETIME, ?, 120)
              AND so.Type = '20'
            GROUP BY st.EntryingDepot
            ORDER BY TotalAmount DESC
        """
        cursor.execute(q_depot, (start_str, end_str))
        depot_names = {
            "002": "Ana Mutfak",
            "003": "Ana Bar",
            "004": "Beach Bar",
            "005": "Pool Bar",
            "006": "Captain Cook Bar",
            "017": "A la Carte Bar",
            "018": "Night Bar",
            "021": "Pastane",
            "024": "Soğuk Mutfak",
            "026": "Kasaphane",
            "028": "Bulaşıkhane",
            "029": "Personel Yemekhane"
        }
        depot_breakdown = [
            {
                "code": str(r[0] or '').strip(),
                "name": depot_names.get(str(r[0] or '').strip(), f"Depo {str(r[0] or '').strip()}"),
                "amount": float(r[1] or 0)
            } for r in cursor.fetchall()
        ]

        # 4c. Waste / Scrap Stock Adjustments (Type 25)
        q_zayi = """
            SELECT 
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
              AND so.Type = '25'
            GROUP BY p.ProductCode, p.Remark, p.Unit
            ORDER BY TotalAmount DESC
        """
        cursor.execute(q_zayi, (start_str, end_str))
        zayi_items = [
            {
                "code": str(r[0] or '').strip(),
                "name": str(r[1] or '').strip(),
                "unit": str(r[2] or '').strip(),
                "qty": float(r[3] or 0),
                "amount": float(r[4] or 0)
            } for r in cursor.fetchall()
        ]
        total_zayi_amount = sum(item["amount"] for item in zayi_items)

        stock_payload["fb_analytics"] = {
            "top10_items": top10_items,
            "depot_breakdown": depot_breakdown,
            "zayi_items": zayi_items,
            "total_zayi_amount": total_zayi_amount
        }

        conn.close()
    except Exception as e:
        print(f"Error fetching live stock data: {e}")
        if conn:
            conn.close()

    return stock_payload

def get_live_data(date_str=None, mode="daily"):
    """
    mode:
      - "daily": Single selected day (e.g. 2026-09-15)
      - "monthly": Full calendar month (1st of month to last day of month)
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        dt = datetime.now()
        date_str = dt.strftime("%Y-%m-%d")
        
    year = dt.year
    month = dt.month
    day = dt.day
    
    _, days_in_month = calendar.monthrange(year, month)
    
    if mode == "monthly":
        start_day = 1
        end_day = days_in_month
        mtd_factor = 1.0
        display_label = f"{year}-{month:02d} (Aylık)"
    else: # daily
        mode = "daily"
        start_day = day
        end_day = day
        mtd_factor = 1.0 / float(days_in_month)
        display_label = f"{year}-{month:02d}-{day:02d} (Günlük)"
    
    iso_start = f"{year:04d}{month:02d}{start_day:02d}"
    iso_end = f"{year:04d}{month:02d}{end_day:02d}"
    
    start_dt_str = f"{year:04d}-{month:02d}-{start_day:02d} 00:00:00"
    end_dt_str = f"{year:04d}-{month:02d}-{end_day:02d} 23:59:59"

    # 1. Fetch stock payload
    stock_payload = fetch_live_stock_data(start_dt_str, end_dt_str)
    
    # Defaults
    ai = 0
    hb = 0
    bb = 0
    neilson = 0
    comp = 0
    paid_excl_neilson = 0
    paid_incl_neilson = 0
    paid_and_comp_excl_neilson = 0
    all_stays = 0
    eur_rate = 55.909183
    gbp_rate = 64.125000
    pos_sales = {}
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Query Overnights
            query_overnights = """
                SELECT 
                    a.AgencyCode,
                    dd.Board,
                    SUM(ISNULL(dd.Pax, 0)) AS pax_nights
                FROM DailyDetail dd
                JOIN Reservation r ON r.RecId = dd.ReservationId
                JOIN Agency a ON a.RecId = r.AgencyId
                WHERE dd.StayDate >= CONVERT(DATETIME, ?, 112) 
                  AND dd.StayDate <= CONVERT(DATETIME, ?, 112) + ' 23:59:59'
                  AND dd.Status != -1 AND r.Status != -1
                GROUP BY a.AgencyCode, dd.Board
            """
            cursor.execute(query_overnights, (iso_start, iso_end))
            rows = cursor.fetchall()
            
            ai = sum(r.pax_nights for r in rows if r.AgencyCode != 'COMP' and r.Board == 'AI')
            hb = sum(r.pax_nights for r in rows if r.AgencyCode != 'COMP' and r.Board == 'HB')
            bb = sum(r.pax_nights for r in rows if r.AgencyCode != 'COMP' and r.Board == 'BB')
            neilson = sum(r.pax_nights for r in rows if 'NEILSON' in (r.AgencyCode or '').upper())
            comp = sum(r.pax_nights for r in rows if r.AgencyCode == 'COMP')
            
            paid_excl_neilson = ai + hb + bb
            paid_incl_neilson = paid_excl_neilson
            paid_and_comp_excl_neilson = paid_excl_neilson + comp
            all_stays = paid_and_comp_excl_neilson
            
            # Query Exchange Rates
            query_eur = """
                SELECT AVG(ISNULL(NULLIF(Invoice, 0), ISNULL(NULLIF(Pos, 0), Buying))) as eur_rate
                FROM ExchangeRate
                WHERE CurrencyCode = 'EUR'
                  AND CurrDate >= CONVERT(DATETIME, ?, 112)
                  AND CurrDate <= CONVERT(DATETIME, ?, 112) + ' 23:59:59'
            """
            cursor.execute(query_eur, (iso_start, iso_end))
            row_eur = cursor.fetchone()
            if row_eur and row_eur[0]:
                eur_rate = float(row_eur[0])
            
            query_gbp = """
                SELECT AVG(ISNULL(NULLIF(Invoice, 0), ISNULL(NULLIF(Pos, 0), Buying))) as gbp_rate
                FROM ExchangeRate
                WHERE CurrencyCode = 'GBP'
                  AND CurrDate >= CONVERT(DATETIME, ?, 112)
                  AND CurrDate <= CONVERT(DATETIME, ?, 112) + ' 23:59:59'
            """
            cursor.execute(query_gbp, (iso_start, iso_end))
            row_gbp = cursor.fetchone()
            if row_gbp and row_gbp[0]:
                gbp_rate = float(row_gbp[0])
            
            # POS Sales Query
            query_pos = """
                SELECT 
                    ps.DepartCode,
                    ISNULL(d.DepartName, ps.DepartCode) AS DepartName,
                    SUM(ISNULL(ps.PriceTotal, 0)) AS TotalPrice,
                    SUM(ISNULL(ps.NetAmount, 0)) AS NetTotal
                FROM PosSummary ps
                LEFT JOIN Department d ON d.DepartCode = ps.DepartCode
                WHERE ps.SellingDate >= CONVERT(DATETIME, ?, 112)
                  AND ps.SellingDate <= CONVERT(DATETIME, ?, 112) + ' 23:59:59'
                GROUP BY ps.DepartCode, d.DepartName
            """
            cursor.execute(query_pos, (iso_start, iso_end))
            rows_pos = cursor.fetchall()
            for r in rows_pos:
                code_str = str(r[0]).strip()
                pos_sales[code_str] = {
                    "name": str(r[1]).strip(),
                    "total_price": float(r[2] or 0),
                    "net_total": float(r[3] or 0)
                }
            
            conn.close()
        except Exception as e:
            print(f"Error querying live data: {e}")
            if conn:
                conn.close()

    return {
        "mode": mode,
        "selected_date": date_str,
        "display_label": display_label,
        "year": year,
        "month": month,
        "day": day,
        "start_day": start_day,
        "end_day": end_day,
        "days_in_month": days_in_month,
        "mtd_factor": mtd_factor,
        "overnights": {
            "AI": ai,
            "HB": hb,
            "BB": bb,
            "Neilson": neilson,
            "Comp": comp,
            "Paid_excl_Neilson": paid_excl_neilson,
            "Paid_incl_Neilson": paid_incl_neilson,
            "Paid_and_Comp_excl_Neilson": paid_and_comp_excl_neilson,
            "All_Stays": all_stays
        },
        "exchange_rates": {
            "EUR": eur_rate,
            "GBP": gbp_rate
        },
        "pos_sales": pos_sales,
        "stock": stock_payload
    }

@app.route("/")
def index():
    all_months = load_all_months_data()
    # Default month is 2026-09 if present, else latest
    available_months = sorted(list(all_months.keys()))
    current_month_key = "2026-09" if "2026-09" in all_months else (available_months[-1] if available_months else "2026-09")
    excel_data = all_months.get(current_month_key, {})
    
    # Default to daily mode on the latest valid date of September 2026 (or today if current)
    today_str = datetime.now().strftime("%Y-%m-%d")
    default_date = "2026-09-30" if "2026-09" in all_months else today_str
    
    live_data = get_live_data(default_date, mode="monthly")
    
    return render_template(
        "index.html", 
        excel_data=excel_data, 
        all_months_data=all_months,
        available_months=available_months,
        current_month_key=current_month_key,
        live_data=live_data, 
        selected_date=default_date
    )

@app.route("/api/live_data")
def api_live_data():
    date_str = request.args.get("date")
    mode = request.args.get("mode", "daily") # "daily" or "monthly"
    
    if not date_str:
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        day = request.args.get("day", type=int)
        if year and month:
            d = day if (day and mode == "daily") else 1
            date_str = f"{year:04d}-{month:02d}-{d:02d}"
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
    return jsonify(get_live_data(date_str, mode=mode))

@app.route("/api/get_month_excel")
def api_get_month_excel():
    month_key = request.args.get("month_key", "2026-09")
    all_months = load_all_months_data()
    return jsonify(all_months.get(month_key, {}))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
