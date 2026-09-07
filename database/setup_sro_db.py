import sqlite3
import os
import uuid
from pathlib import Path

DB_PATH = Path(__file__).with_name("sro_housing.db")

def create_sro_schema(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. SRO Hotels Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sro_hotels (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        former_name TEXT,
        street_address TEXT NOT NULL,
        year_built INTEGER,
        year_acquired_or_opened INTEGER,
        original_class TEXT, -- 'Palace Hotel', 'Middle-Class Hotel', 'Working-Class Hotel'
        current_owner_operator TEXT NOT NULL, -- 'SRO Housing Corporation', 'AIDS Healthcare Foundation', 'Skid Row Housing Trust (In Receivership)', etc.
        total_units INTEGER,
        monthly_rent_usd REAL,
        funding_notes TEXT,
        current_status TEXT NOT NULL CHECK (current_status IN ('Operating', 'In Receivership', 'Pending Demolition', 'Under Rehabilitation', 'Pending Conversion'))
    );
    """)

    # 2. SRO Habitability and Code Violations Table (based on lawsuits and inspections in the sources)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habitability_violations (
        id TEXT PRIMARY KEY,
        hotel_id TEXT REFERENCES sro_hotels(id) ON DELETE CASCADE,
        category TEXT NOT NULL CHECK (category IN ('Infestation', 'Plumbing/Sewage', 'Structural/Crumbling', 'Elevator', 'Security/Trespass', 'Safety/Smoke Detectors', 'Unaddressed Death Trauma')),
        description TEXT NOT NULL,
        severity TEXT NOT NULL CHECK (severity IN ('Low', 'Moderate', 'Severe', 'Inhumane/Critical')),
        documented_date TEXT NOT NULL, -- YYYY-MM-DD
        source_reference TEXT NOT NULL, -- e.g., 'Washington v. Renato Apartments, LP Lawsuit'
        resolution_status TEXT NOT NULL CHECK (resolution_status IN ('Active Violation', 'Under Litigation', 'Resolved'))
    );
    """)

    # 3. SRO Financial and Operational Performance Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sro_financials (
        id TEXT PRIMARY KEY,
        operator_name TEXT NOT NULL, -- e.g., 'SRO Housing Corporation', 'AIDS Healthcare Foundation (AHF)', 'Skid Row Housing Trust'
        total_portfolio_units INTEGER,
        estimated_financial_loss_usd REAL,
        loss_timeframe TEXT,
        operational_status_summary TEXT,
        source_reference TEXT
    );
    """)

    # 4. SRO Historical Significance Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sro_history (
        id TEXT PRIMARY KEY,
        hotel_id TEXT REFERENCES sro_hotels(id) ON DELETE CASCADE,
        notable_figures_or_events TEXT NOT NULL, -- e.g., 'John Fante set Ask the Dust here', 'James M. Cain research spot'
        historical_details TEXT NOT NULL
    );
    """)

    conn.commit()
    print("SRO Housing Database tables created successfully.")

def seed_sro_data(conn):
    cursor = conn.cursor()
    
    # Generate UUIDs for hotels to maintain strong relational integrity
    renato_id = str(uuid.uuid4())
    king_eddy_id = str(uuid.uuid4())
    baltimore_id = str(uuid.uuid4())
    barclay_id = str(uuid.uuid4())
    madison_id = str(uuid.uuid4())
    
    hotels = [
        (renato_id, "Renato Apartments", "Renato Hotel", "Renato Apartments, Skid Row, Los Angeles, CA", 1920, 2010, "Working-Class Hotel", "SRO Housing Corporation", 96, 450.0, "Built utilizing a $9.5 million loan from the City of Los Angeles. Rent subsidized by HACLA.", "Operating"),
        (king_eddy_id, "King Edward Hotel", "King Eddy Hotel", "5th St and Los Angeles St, Los Angeles, CA 90013", 1906, 2018, "Palace Hotel", "AIDS Healthcare Foundation", 150, 400.0, "Acquired by AHF's Healthy Housing Foundation. Operates single rooms with shared facilities.", "Operating"),
        (baltimore_id, "Baltimore Hotel", "Hotel Baltimore", "5th St and Los Angeles St, Los Angeles, CA 90013", 1910, 2017, "Middle-Class Hotel", "AIDS Healthcare Foundation", 215, 400.0, "Acquired by AHF. Operates low-barrier SRO units.", "Operating"),
        (barclay_id, "Barclay Hotel", "The Van Nuys Hotel", "103 W 4th St, Los Angeles, CA 90013", 1896, 2018, "Palace Hotel", "AIDS Healthcare Foundation", 158, 400.0, "The first luxury 'palace' hotel in western downtown, later converted to rooming house levels.", "Operating"),
        (madison_id, "Madison Hotel", "The Madison", "Madison Hotel, 7th St, Los Angeles, CA", 1920, 2018, "Working-Class Hotel", "AIDS Healthcare Foundation", 200, 400.0, "AHF SRO providing single rooms with shared showers.", "Operating")
    ]
    
    cursor.executemany("""
        INSERT INTO sro_hotels (id, name, former_name, street_address, year_built, year_acquired_or_opened, original_class, current_owner_operator, total_units, monthly_rent_usd, funding_notes, current_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, hotels)
    
    # Seed SRO Habitability and Code Violations (from Washington v. Renato Apartments, LP filed on Dec 12, 2024)
    violations = [
        (str(uuid.uuid4()), renato_id, "Plumbing/Sewage", "Raw sewage flooding directly into tenants' units; unaddressed leaks.", "Inhumane/Critical", "2024-12-12", "Washington v. Renato Apartments, LP Lawsuit", "Under Litigation"),
        (str(uuid.uuid4()), renato_id, "Elevator", "Broken elevators causing long-term non-accessibility for disabled and elderly seniors.", "Severe", "2024-12-12", "Washington v. Renato Apartments, LP Lawsuit", "Under Litigation"),
        (str(uuid.uuid4()), renato_id, "Infestation", "Rampant and long-term bedbug and cockroach infestations left untreated.", "Severe", "2024-12-12", "Washington v. Renato Apartments, LP Lawsuit", "Under Litigation"),
        (str(uuid.uuid4()), renato_id, "Structural/Crumbling", "Crumbling walls and ceilings with active water intrusion.", "Moderate", "2024-12-12", "Washington v. Renato Apartments, LP Lawsuit", "Under Litigation"),
        (str(uuid.uuid4()), renato_id, "Safety/Smoke Detectors", "Inoperable smoke detectors throughout the residential facility.", "Severe", "2024-12-12", "Washington v. Renato Apartments, LP Lawsuit", "Under Litigation"),
        (str(uuid.uuid4()), renato_id, "Security/Trespass", "Unsecured doors and windows allowing trespassers to commit vandalism and theft inside hallways.", "Severe", "2024-12-12", "Washington v. Renato Apartments, LP Lawsuit", "Under Litigation"),
        (str(uuid.uuid4()), renato_id, "Unaddressed Death Trauma", "Decorated veteran committed suicide by jumping from the 5th floor into the courtyard. Tenants forced to walk past his mangled body for hours. Management failed to clean up blood/matter, forcing tenants to clean it themselves.", "Inhumane/Critical", "2024-12-12", "Washington v. Renato Apartments, LP Lawsuit", "Under Litigation"),
        (str(uuid.uuid4()), king_eddy_id, "Infestation", "AHF-managed property cited for persistent cockroach infestations.", "Moderate", "2023-11-17", "Los Angeles Times Investigation (Nov 2023)", "Active Violation"),
        (str(uuid.uuid4()), king_eddy_id, "Plumbing/Sewage", "Clogged toilets and failing plumbing infrastructure.", "Moderate", "2023-11-17", "Los Angeles Times Investigation (Nov 2023)", "Active Violation")
    ]
    
    cursor.executemany("""
        INSERT INTO habitability_violations (id, hotel_id, category, description, severity, documented_date, source_reference, resolution_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, violations)
    
    # Seed SRO Financial and Operational Performance Table (based on receiverships and losses)
    financials = [
        (str(uuid.uuid4()), "Skid Row Housing Trust", 1200, 500000000.0, "2023 (Financial Collapse)", "Collapsed into complete receivership in April 2023. Out of 29 properties, 10 SRO buildings are now targeted for demolition or conversion. Estimated portfolio repair cost is $500M.", "Court Receivership Documents / iHFG White Paper"),
        (str(uuid.uuid4()), "AIDS Healthcare Foundation (AHF)", 1600, 15000000.0, "6 Years (2017-2023)", "Spent nearly $200M acquiring properties and $30M on repairs. Reported over $15M in operational losses due to high costs of retrofitting century-old hotels.", "AHF Corporate Disclosures / Real Deal Report"),
        (str(uuid.uuid4()), "SRO Housing Corporation", 2500, 0.0, "Ongoing", "Operates 15 SRO buildings in Skid Row, but reports that 10 of those 15 buildings are actively operating at an operational loss.", "SRO Housing Corporation Annual Audit")
    ]
    
    cursor.executemany("""
        INSERT INTO sro_financials (id, operator_name, total_portfolio_units, estimated_financial_loss_usd, loss_timeframe, operational_status_summary, source_reference)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, financials)
    
    # Seed SRO History Table
    history = [
        (str(uuid.uuid4()), king_eddy_id, "John Fante - Ask the Dust", "The King Edward Hotel's basement saloon (King Eddy Saloon) served as the primary setting and inspiration for John Fante's legendary 1939 novel 'Ask the Dust'."),
        (str(uuid.uuid4()), king_eddy_id, "James M. Cain - Research Spot", "Famed hardboiled novelist James M. Cain spent considerable time at the King Edward Saloon researching characters and local color for his classic book 'The Postman Always Rings Twice'.")
    ]
    
    cursor.executemany("""
        INSERT INTO sro_history (id, hotel_id, notable_figures_or_events, historical_details)
        VALUES (?, ?, ?, ?);
    """, history)
    
    conn.commit()
    print("SRO Housing seed data successfully inserted.")

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    create_sro_schema(conn)
    seed_sro_data(conn)
    conn.close()
