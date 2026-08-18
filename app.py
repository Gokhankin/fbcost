import os
import json
import calendar
import pyodbc
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

FALLBACK_DATA = {
    "overnights": {
        "AI": 1307,
        "HB": 1203,
        "BB": 436,
        "Neilson": 910,
        "Comp": 180,
        "Paid_excl_Neilson": 2946,
        "Paid_incl_Neilson": 3856,
        "Paid_and_Comp_excl_Neilson": 3126,
        "All_Stays": 4036
    },
    "exchange_rates": {
        "EUR": 53.187703,
        "GBP": 61.456363
    },
    "pos_sales": {},
    "stock": {
        "fb_totals": {
            "food": 1232214.05,
            "beverage": 718857.11,
            "alcohol": 219897.89,
            "staff": 210913.13,
            "staff_food": 191854.53,
            "staff_bev": 7794.78,
            "staff_alc": 11263.82,
            "total": 2381882.18
        },
        "detayli_stok": [],
        "personel_stok": []
    }
}

def get_db_connection():
    conn_str = os.getenv("DB_CONNECTION_STRING") or os.getenv("CONN_STR") or "DRIVER={ODBC Driver 18 for SQL Server};SERVER=192.168.0.41,1433;DATABASE=SednaAdakoy;UID=gokhan;PWD=Ad!!2025!!;TrustServerCertificate=yes;"
    if not conn_str:
        return None
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

    # Try FreeTDS first (works on Linux)
    freetds_str = "DRIVER=FreeTDS;SERVER=10.0.0.11;PORT=1433;DATABASE=ANTMARINSEDNA2021;UID=sa;PWD=00-0C-29-35-5A-D3;TDS_Version=7.4;"
    try:
        return pyodbc.connect(freetds_str, timeout=3)
    except Exception:
        pass

    # Fallback to ODBC Driver 18 / 17 (Windows environment)
    ms_str = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=10.0.0.11,1433;DATABASE=ANTMARINSEDNA2021;UID=sa;PWD=00-0C-29-35-5A-D3;TrustServerCertificate=yes;"
    try:
        return pyodbc.connect(ms_str, timeout=3)
    except Exception as e:
        print(f"Stock DB connection error: {e}")
        return None

def fetch_live_stock_data(start_str, end_str):
    conn = get_stock_db_connection()
    if not conn:
        return FALLBACK_DATA["stock"]

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

        conn.close()
    except Exception as e:
        print(f"Error fetching live stock data: {e}")
        if conn:
            conn.close()
        stock_payload = FALLBACK_DATA["stock"]

    return stock_payload

def get_live_data(date_str=None):
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
    mtd_factor = round(day / float(days_in_month), 4)
    
    iso_start = f"{year:04d}{month:02d}01"
    iso_end = f"{year:04d}{month:02d}{day:02d}"
    
    start_dt_str = f"{year:04d}-{month:02d}-01 00:00:00"
    end_dt_str = f"{year:04d}-{month:02d}-{day:02d} 23:59:59"

    # Fetch live stock payload from 10.0.0.11 (ANTMARINSEDNA2021)
    stock_payload = fetch_live_stock_data(start_dt_str, end_dt_str)
    
    conn = get_db_connection()
    if not conn:
        print("Using fallback database values for overnights/POS.")
        res = dict(FALLBACK_DATA)
        res["selected_date"] = date_str
        res["day_of_month"] = day
        res["days_in_month"] = days_in_month
        res["mtd_factor"] = mtd_factor
        res["stock"] = stock_payload
        return res
    
    try:
        cursor = conn.cursor()
        
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
        
        ai = sum(r.pax_nights for r in rows if r.AgencyCode != 'COMP' and 'NEILSON' not in (r.AgencyCode or '').upper() and r.Board == 'AI')
        hb = sum(r.pax_nights for r in rows if r.AgencyCode != 'COMP' and 'NEILSON' not in (r.AgencyCode or '').upper() and r.Board == 'HB')
        bb = sum(r.pax_nights for r in rows if r.AgencyCode != 'COMP' and 'NEILSON' not in (r.AgencyCode or '').upper() and r.Board == 'BB')
        neilson = sum(r.pax_nights for r in rows if 'NEILSON' in (r.AgencyCode or '').upper() and r.Board == 'BB')
        comp = sum(r.pax_nights for r in rows if r.AgencyCode == 'COMP')
        
        paid_excl_neilson = ai + hb + bb
        paid_incl_neilson = paid_excl_neilson + neilson
        paid_and_comp_excl_neilson = paid_excl_neilson + comp
        all_stays = paid_incl_neilson + comp
        
        if paid_excl_neilson == 0:
            paid_excl_neilson = int(FALLBACK_DATA["overnights"]["Paid_excl_Neilson"] * mtd_factor)
            paid_incl_neilson = int(FALLBACK_DATA["overnights"]["Paid_incl_Neilson"] * mtd_factor)
            paid_and_comp_excl_neilson = int(FALLBACK_DATA["overnights"]["Paid_and_Comp_excl_Neilson"] * mtd_factor)
            all_stays = int(FALLBACK_DATA["overnights"]["All_Stays"] * mtd_factor)
            ai = int(FALLBACK_DATA["overnights"]["AI"] * mtd_factor)
            hb = int(FALLBACK_DATA["overnights"]["HB"] * mtd_factor)
            bb = int(FALLBACK_DATA["overnights"]["BB"] * mtd_factor)
            neilson = int(FALLBACK_DATA["overnights"]["Neilson"] * mtd_factor)
            comp = int(FALLBACK_DATA["overnights"]["Comp"] * mtd_factor)

        query_eur = """
            SELECT TOP 1 
                ISNULL(NULLIF(Invoice, 0), ISNULL(NULLIF(Pos, 0), Buying)) as eur_rate
            FROM ExchangeRate
            WHERE CurrencyCode = 'EUR'
              AND CurrDate <= CONVERT(DATETIME, ?, 112) + ' 23:59:59'
            ORDER BY CurrDate DESC
        """
        cursor.execute(query_eur, (iso_end,))
        row_eur = cursor.fetchone()
        eur_rate = float(row_eur[0]) if row_eur and row_eur[0] else FALLBACK_DATA["exchange_rates"]["EUR"]
        
        query_gbp = """
            SELECT TOP 1
                ISNULL(NULLIF(Invoice, 0), ISNULL(NULLIF(Pos, 0), Buying)) as gbp_rate
            FROM ExchangeRate
            WHERE CurrencyCode = 'GBP'
              AND CurrDate <= CONVERT(DATETIME, ?, 112) + ' 23:59:59'
            ORDER BY CurrDate DESC
        """
        cursor.execute(query_gbp, (iso_end,))
        row_gbp = cursor.fetchone()
        gbp_rate = float(row_gbp[0]) if row_gbp and row_gbp[0] else FALLBACK_DATA["exchange_rates"]["GBP"]
        
        # Live POS Sales Query from Sedna SQL
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
        pos_sales = {}
        for r in rows_pos:
            code_str = str(r[0]).strip()
            pos_sales[code_str] = {
                "name": str(r[1]).strip(),
                "total_price": float(r[2] or 0),
                "net_total": float(r[3] or 0)
            }
        
        conn.close()
        
        return {
            "selected_date": date_str,
            "day_of_month": day,
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
        
    except Exception as e:
        print(f"Error querying live data: {e}")
        if conn:
            conn.close()
        res = dict(FALLBACK_DATA)
        res["selected_date"] = date_str
        res["day_of_month"] = day
        res["days_in_month"] = days_in_month
        res["mtd_factor"] = mtd_factor
        res["stock"] = stock_payload
        return res

def load_excel_data():
    json_path = os.path.join(os.path.dirname(__file__), "fbcost_data.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.route("/")
def index():
    excel_data = load_excel_data()
    today_str = datetime.now().strftime("%Y-%m-%d")
    live_data = get_live_data(today_str)
    return render_template("index.html", excel_data=excel_data, live_data=live_data, selected_date=today_str)

@app.route("/api/live_data")
def api_live_data():
    date_str = request.args.get("date")
    if not date_str:
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        if year and month:
            date_str = f"{year:04d}-{month:02d}-01"
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
    return jsonify(get_live_data(date_str))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
