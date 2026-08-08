import os
import json
import pyodbc
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Load env variables
load_dotenv()

app = Flask(__name__)

# Fallback values if database connection fails
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

def get_live_data(year=2026, month=6):
    conn = get_db_connection()
    if not conn:
        print("Using fallback database values.")
        return FALLBACK_DATA
    
    try:
        cursor = conn.cursor()
        
        # 1. Fetch overnights
        query_overnights = """
            SELECT 
                a.AgencyCode,
                dd.Board,
                SUM(ISNULL(dd.Pax, 0)) AS pax_nights
            FROM DailyDetail dd
            JOIN Reservation r ON r.RecId = dd.ReservationId
            JOIN Agency a ON a.RecId = r.AgencyId
            WHERE YEAR(dd.StayDate) = ? AND MONTH(dd.StayDate) = ?
              AND dd.Status != -1 AND r.Status != -1
            GROUP BY a.AgencyCode, dd.Board
        """
        cursor.execute(query_overnights, (year, month))
        rows = cursor.fetchall()
        
        ai = 0
        hb = 0
        bb = 0
        neilson = 0
        comp = 0
        
        for r in rows:
            agency = r.AgencyCode or ''
            board = r.Board or ''
            pax = int(r.pax_nights or 0)
            
            if agency == 'COMP':
                comp += pax
            elif 'NEILSON' in agency.upper() and board == 'BB':
                neilson += pax
            else:
                # Neilson AI and HB stays are included in AI/HB totals
                if board == 'AI':
                    ai += pax
                elif board == 'HB':
                    hb += pax
                else:
                    bb += pax
                
        paid_excl_neilson = ai + hb + bb
        paid_incl_neilson = paid_excl_neilson + neilson
        paid_and_comp_excl_neilson = paid_excl_neilson + comp
        all_stays = paid_incl_neilson + comp
        
        # 2. Fetch EUR rate
        query_eur = """
            SELECT 
                AVG(ISNULL(NULLIF(Invoice, 0), ISNULL(NULLIF(Pos, 0), Buying))) as avg_eur_rate
            FROM ExchangeRate
            WHERE CurrencyCode = 'EUR'
              AND YEAR(CurrDate) = ?
              AND MONTH(CurrDate) = ?
        """
        cursor.execute(query_eur, (year, month))
        eur_val = cursor.fetchone()[0]
        eur_rate = float(eur_val) if eur_val else FALLBACK_DATA["exchange_rates"]["EUR"]
        
        # 3. Fetch GBP rate
        query_gbp = """
            SELECT 
                AVG(ISNULL(NULLIF(Invoice, 0), ISNULL(NULLIF(Pos, 0), Buying))) as avg_gbp_rate
            FROM ExchangeRate
            WHERE CurrencyCode = 'GBP'
              AND YEAR(CurrDate) = ?
              AND MONTH(CurrDate) = ?
        """
        cursor.execute(query_gbp, (year, month))
        gbp_val = cursor.fetchone()[0]
        gbp_rate = float(gbp_val) if gbp_val else FALLBACK_DATA["exchange_rates"]["GBP"]
        
        conn.close()
        
        return {
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
            }
        }
        
    except Exception as e:
        print(f"Error querying live data: {e}")
        if conn:
            conn.close()
        return FALLBACK_DATA

# Load Excel data from JSON file
def load_excel_data():
    json_path = os.path.join(os.path.dirname(__file__), "fbcost_data.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.route("/")
def index():
    excel_data = load_excel_data()
    live_data = get_live_data(2026, 6)
    return render_template("index.html", excel_data=excel_data, live_data=live_data)

@app.route("/api/live_data")
def api_live_data():
    year = request.args.get("year", 2026, type=int)
    month = request.args.get("month", 6, type=int)
    return jsonify(get_live_data(year, month))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
