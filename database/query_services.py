import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("recovery_app.db")

def query_beds_and_placements(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    print("\n==========================================")
    print("      REAL-TIME ECOSYSTEM DASHBOARD")
    print("==========================================\n")
    
    # Query Bed Availability
    cursor.execute("""
        SELECT name, facility_type, total_capacity, available_beds 
        FROM facilities;
    """)
    facilities = cursor.fetchall()
    
    print("--- DETOX & HOUSING CAPACITIES (AVAILABLE BEDS) ---")
    for name, fac_type, capacity, beds in facilities:
        print(f"• Facility: {name:<35} | Type: {fac_type:<18} | Capacity: {capacity:<3} | Available Beds: {beds:<3}")
        
    print("\n--- ACTIVE CLIENT PLACEMENTS & RECOVERY TRACKS ---")
    cursor.execute("""
        SELECT y.alias, f.name, p.placement_type, p.status, p.start_date
        FROM program_placements p
        JOIN youth_profiles y ON p.youth_id = y.id
        JOIN facilities f ON p.facility_id = f.id;
    """)
    placements = cursor.fetchall()
    
    if not placements:
        print("No clients are currently booked or enrolled in placements.")
    for alias, facility, p_type, status, start_date in placements:
        print(f"• Youth Alias: '{alias:<10}' | Placed At: {facility:<30} | Track: {p_type:<12} | Status: {status:<10} | Since: {start_date}")
        
    print("\n--- ACTIVE MEDICATION-ASSISTED TREATMENT (MAT) RECIPIENTS ---")
    cursor.execute("""
        SELECT y.alias, m.medication_name, m.dosage_instructions, c.full_name, m.adherence_status
        FROM mat_prescriptions m
        JOIN youth_profiles y ON m.youth_id = y.id
        JOIN clinicians c ON m.prescribing_clinician_id = c.id;
    """)
    mats = cursor.fetchall()
    
    if not mats:
        print("No active MAT prescriptions mapped in database.")
    for alias, med, dosage, doctor, status in mats:
        print(f"• Youth Alias: '{alias:<10}' | Medication: {med:<15} | Dosage: {dosage:<50} | MD: {doctor:<25} | Status: {status}")
        
    print("\n==========================================\n")
    conn.close()

if __name__ == "__main__":
    query_beds_and_placements(DB_PATH)
