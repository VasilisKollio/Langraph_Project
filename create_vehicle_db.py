import sqlite3

# Your provided data as a list of dicts
vehicles = [
    {'owner_name': 'David Johnson', 'type': 'Car', 'brand': 'Nissan', 'color': 'White', 'license_plate': 'ABX-2391', 'status': 'Impounded', 'fines': 5},
    {'owner_name': 'David Johnson', 'type': 'Car', 'brand': 'Volkswagen', 'color': 'Red', 'license_plate': 'KLY-7743', 'status': 'Stolen', 'fines': 0},
    {'owner_name': 'John Smith', 'type': 'Car', 'brand': 'Honda', 'color': 'Grey', 'license_plate': 'MNP-1122', 'status': 'Inactive', 'fines': 0},
    {'owner_name': 'Anna Davis', 'type': 'Car', 'brand': 'BMW', 'color': 'Black', 'license_plate': 'TUV-9831', 'status': 'Active', 'fines': 4},
    {'owner_name': 'Anna Davis', 'type': 'Car', 'brand': 'BMW', 'color': 'Blue', 'license_plate': 'ZXD-4431', 'status': 'Active', 'fines': 3},
    {'owner_name': 'David Brown', 'type': 'Car', 'brand': 'Mercedes', 'color': 'Silver', 'license_plate': 'VET-6519', 'status': 'Active', 'fines': 0},
    {'owner_name': 'Michael Martinez', 'type': 'Car', 'brand': 'Subaru', 'color': 'Black', 'license_plate': 'RAN-1234', 'status': 'Stolen', 'fines': 0},
    {'owner_name': 'Alex Miller', 'type': 'Car', 'brand': 'Volkswagen', 'color': 'Grey', 'license_plate': 'LPA-4527', 'status': 'Active', 'fines': 2},
    {'owner_name': 'Jane Garcia', 'type': 'Car', 'brand': 'Ford', 'color': 'Red', 'license_plate': 'MEX-7081', 'status': 'Impounded', 'fines': 4},
    {'owner_name': 'Michael Wilson', 'type': 'Car', 'brand': 'Subaru', 'color': 'Silver', 'license_plate': 'QWE-8811', 'status': 'Impounded', 'fines': 2},
    {'owner_name': 'Jane Wilson', 'type': 'Car', 'brand': 'Kia', 'color': 'Black', 'license_plate': 'BZX-9081', 'status': 'Active', 'fines': 3},
    {'owner_name': 'Sarah Brown', 'type': 'Car', 'brand': 'Subaru', 'color': 'Green', 'license_plate': 'PKL-4422', 'status': 'Inactive', 'fines': 2},
    {'owner_name': 'Sarah Wilson', 'type': 'Car', 'brand': 'Mazda', 'color': 'Yellow', 'license_plate': 'HKB-8626', 'status': 'Active', 'fines': 3},
    {'owner_name': 'Alex Garcia', 'type': 'Car', 'brand': 'Jeep', 'color': 'Silver', 'license_plate': 'IAG-3128', 'status': 'Active', 'fines': 0},
    {'owner_name': 'Michael Brown', 'type': 'Car', 'brand': 'BMW', 'color': 'Silver', 'license_plate': 'RXK-2021', 'status': 'Active', 'fines': 5},
    {'owner_name': 'Emily Wilson', 'type': 'Car', 'brand': 'Ford', 'color': 'Grey', 'license_plate': 'FHB-8302', 'status': 'Active', 'fines': 2},
    {'owner_name': 'Michael Smith', 'type': 'Car', 'brand': 'Jeep', 'color': 'Red', 'license_plate': 'ZEQ-0540', 'status': 'Inactive', 'fines': 1},
    {'owner_name': 'Jane Smith', 'type': 'Car', 'brand': 'Volkswagen', 'color': 'Silver', 'license_plate': 'QXS-9118', 'status': 'Stolen', 'fines': 4},
    {'owner_name': 'Laura Davis', 'type': 'Car', 'brand': 'Nissan', 'color': 'White', 'license_plate': 'QER-4038', 'status': 'Stolen', 'fines': 2},
    {'owner_name': 'Emily Brown', 'type': 'Car', 'brand': 'Kia', 'color': 'White', 'license_plate': 'HOL-7324', 'status': 'Inactive', 'fines': 1},
    {'owner_name': 'Chris Brown', 'type': 'Car', 'brand': 'Jeep', 'color': 'White', 'license_plate': 'PZG-7925', 'status': 'Active', 'fines': 4},
    {'owner_name': 'Sarah Smith', 'type': 'Car', 'brand': 'Volkswagen', 'color': 'Red', 'license_plate': 'UBS-3565', 'status': 'Impounded', 'fines': 2},
    {'owner_name': 'Anna Wilson', 'type': 'Car', 'brand': 'Mazda', 'color': 'Blue', 'license_plate': 'QWO-6134', 'status': 'Inactive', 'fines': 3},
    {'owner_name': 'Michael Davis', 'type': 'Car', 'brand': 'Nissan', 'color': 'Red', 'license_plate': 'OTL-7243', 'status': 'Active', 'fines': 5},
    {'owner_name': 'Michael Johnson', 'type': 'Car', 'brand': 'Chevrolet', 'color': 'Red', 'license_plate': 'OFX-1934', 'status': 'Inactive', 'fines': 4},
    {'owner_name': 'Jane Davis', 'type': 'Car', 'brand': 'Mercedes', 'color': 'Red', 'license_plate': 'BDW-6383', 'status': 'Impounded', 'fines': 2},
    {'owner_name': 'Alex Smith', 'type': 'Car', 'brand': 'Honda', 'color': 'Silver', 'license_plate': 'UHB-6182', 'status': 'Active', 'fines': 1},
    {'owner_name': 'David Martinez', 'type': 'Car', 'brand': 'Mercedes', 'color': 'Blue', 'license_plate': 'OJB-4639', 'status': 'Stolen', 'fines': 2},
    {'owner_name': 'Chris Smith', 'type': 'Car', 'brand': 'Audi', 'color': 'Black', 'license_plate': 'PFS-1740', 'status': 'Stolen', 'fines': 0},
    {'owner_name': 'Laura Davis', 'type': 'Car', 'brand': 'Jeep', 'color': 'Silver', 'license_plate': 'RFJ-4054', 'status': 'Active', 'fines': 1},
    {'owner_name': 'Laura Miller', 'type': 'Car', 'brand': 'Mercedes', 'color': 'Red', 'license_plate': 'BWM-5082', 'status': 'Active', 'fines': 1},
    {'owner_name': 'Sarah Johnson', 'type': 'Car', 'brand': 'Toyota', 'color': 'Yellow', 'license_plate': 'BSE-4638', 'status': 'Inactive', 'fines': 3},
]

def create_database():
    conn = sqlite3.connect("police_db.db")
    cursor = conn.cursor()

    # Drop the table if it already exists
    cursor.execute("DROP TABLE IF EXISTS vehicles")

    # Create the table WITHOUT AUTOINCREMENT
    cursor.execute('''
        CREATE TABLE vehicles (
            vehicle_id INTEGER PRIMARY KEY,
            owner_name TEXT NOT NULL,
            type TEXT NOT NULL,
            brand TEXT NOT NULL,
            color TEXT NOT NULL,
            license_plate TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL,
            fines INTEGER NOT NULL
        )
    ''')
    conn.commit()
    return conn, cursor

def insert_vehicle(cursor, vehicle):
    cursor.execute('''
        INSERT OR IGNORE INTO vehicles (owner_name, type, brand, color, license_plate, status, fines)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        vehicle['owner_name'],
        vehicle['type'],
        vehicle['brand'],
        vehicle['color'],
        vehicle['license_plate'],
        vehicle['status'],
        vehicle['fines']
    ))

def main():
    conn, cursor = create_database()
    for v in vehicles:
        insert_vehicle(cursor, v)
    conn.commit()
    conn.close()
    print("Database 'police_db.db' created and populated.")

if __name__ == "__main__":
    main()
