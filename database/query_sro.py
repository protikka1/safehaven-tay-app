import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("sro_housing.db")

def query_sro_housing(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    print("\n==========================================================================")
    print("                      SKID ROW SRO HOUSING INVENTORY")
    print("==========================================================================\n")
    
    # 1. Query SRO Hotels
    cursor.execute("""
        SELECT name, year_built, current_owner_operator, total_units, monthly_rent_usd, current_status 
        FROM sro_hotels;
    """)
    hotels = cursor.fetchall()
    
    print("--- INDIVIDUAL SRO PROPERTY DIRECTORY ---")
    for name, year, owner, units, rent, status in hotels:
        print(f"• Hotel: {name:<20} | Built: {year:<4} | Operator: {owner:<26} | Units: {units:<3} | Rent: ${rent:<5.2f} | Status: {status}")
        
    # 2. Query Habitability Violations & Lawsuits
    print("\n--- CRITICAL HABITABILITY VIOLATIONS & LAWSUITS ---")
    cursor.execute("""
        SELECT h.name, v.category, v.severity, v.resolution_status, v.description, v.source_reference
        FROM habitability_violations v
        JOIN sro_hotels h ON v.hotel_id = h.id;
    """)
    violations = cursor.fetchall()
    
    for name, category, severity, status, desc, source in violations:
        print(f"\n[HOTEL: {name}]")
        print(f"  - Category: {category:<20} | Severity: {severity:<15} | Status: {status}")
        print(f"  - Description: {desc}")
        print(f"  - Source: {source}")

    # 3. Query Financial & Receivership Realities
    print("\n--- SRO OPERATOR FINANCIAL CRISIS & RECEIVERSHIPS ---")
    cursor.execute("""
        SELECT operator_name, total_portfolio_units, estimated_financial_loss_usd, loss_timeframe, operational_status_summary
        FROM sro_financials;
    """)
    financials = cursor.fetchall()
    
    for operator, units, loss, timeframe, summary in financials:
        loss_str = f"${loss:,.2f}" if loss > 0 else "N/A"
        print(f"\n• Operator: {operator}")
        print(f"  - Portfolio Units: {units:<5} | Est. Losses: {loss_str:<15} | Timeframe: {timeframe}")
        print(f"  - Status Summary: {summary}")
        
    # 4. Query Historical / Literary Landmarks
    print("\n--- HISTORICAL & LITERARY SRO LANDMARKS ---")
    cursor.execute("""
        SELECT h.name, s.notable_figures_or_events, s.historical_details
        FROM sro_history s
        JOIN sro_hotels h ON s.hotel_id = h.id;
    """)
    history = cursor.fetchall()
    
    for name, figures, details in history:
        print(f"\n• SRO Site: {name:<20} | Landmark Event: {figures}")
        print(f"  - Details: {details}")
        
    print("\n==========================================================================\n")
    conn.close()

if __name__ == "__main__":
    query_sro_housing(DB_PATH)
