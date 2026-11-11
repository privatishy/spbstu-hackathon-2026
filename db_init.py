import sqlite3
import csv
import time



def insert_data_from_csv(file_name, table_name, columns, query):
    try:
        connection = sqlite3.connect('HackatonDB.db', timeout=10)
        cursor = connection.cursor()
        
        with open(file_name, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            
            data = [tuple(row) for row in reader]
            
            cursor.executemany(query, data)
            connection.commit()
            
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            for attempt in range(3):
                time.sleep(2)
                insert_data_from_csv(file_name, table_name, columns, query) 
            
    finally:
        if connection:
            connection.close()

                 
connection = sqlite3.connect('HackatonDB.db')
cursor = connection.cursor()

cursor.execute("PRAGMA foreign_keys = ON")
    
                     
cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id TEXT PRIMARY KEY,
        supplier_name TEXT NOT NULL,
        delivery_cost_rub INTEGER NOT NULL,
        delivery_days INTEGER NOT NULL
    )
''')
    
                      
cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipment (
        equipment_id TEXT PRIMARY KEY,
        model_name TEXT NOT NULL,
        equipment_type TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        capacity_unit TEXT NOT NULL,
        min_operating_temperature_c INTEGER NOT NULL,
        installation_days INTEGER NOT NULL
    )
''')
    
                     
cursor.execute('''
    CREATE TABLE IF NOT EXISTS offers (
        offer_id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        equipment_id TEXT NOT NULL,
        equipment_type TEXT NOT NULL,
        unit_price_rub INTEGER NOT NULL,
        stock_quantity INTEGER NOT NULL,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE CASCADE,
        FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE
    )
''')
    
                 
cursor.execute('''
    CREATE TABLE IF NOT EXISTS station_1 (
        station_id TEXT NOT NULL,
        station_name TEXT NOT NULL,
        recommended_budget_rub INTEGER NOT NULL,
        deadline_days INTEGER NOT NULL,
        object_id TEXT NOT NULL,
        object_name TEXT NOT NULL,
        optional TEXT CHECK(optional IN ('yes', 'no')) NOT NULL,
        equipment_type TEXT NOT NULL,
        required_capacity INTEGER NOT NULL,
        capacity_unit TEXT NOT NULL,
        operating_temperature_c INTEGER NOT NULL,
        installed_equipment_id TEXT,
        available_capacity INTEGER,
        PRIMARY KEY (station_id, object_id, equipment_type),
        FOREIGN KEY (installed_equipment_id) REFERENCES equipment(equipment_id) ON DELETE SET NULL
    )
''')


connection.commit()
connection.close()

                         
insert_data_from_csv(
    'csv_file\equipment.csv',
    'equipment',
    ['equipment_id', 'model_name', 'equipment_type', 'capacity', 'capacity_unit', 'min_operating_temperature_c', 'installation_days'],
    "INSERT OR IGNORE INTO equipment (equipment_id, model_name, equipment_type, capacity, capacity_unit, min_operating_temperature_c, installation_days) VALUES (?, ?, ?, ?, ?, ?, ?)"
)

insert_data_from_csv(
    'csv_file\offers.csv',
    'offers',
    ['offer_id', 'supplier_id', 'equipment_id', 'equipment_type', 'unit_price_rub', 'stock_quantity'],
    "INSERT OR IGNORE INTO offers (offer_id, supplier_id, equipment_id, equipment_type, unit_price_rub, stock_quantity) VALUES (?, ?, ?, ?, ?, ?)"
)
insert_data_from_csv(
    'csv_file\station_1.csv',
    'station_1',
    ['station_id', 'station_name', 'recommended_budget_rub', 'deadline_days', 'object_id', 'object_name', 'optional', 'equipment_type', 'required_capacity', 'capacity_unit', 'operating_temperature_c', 'installed_equipment_id', 'available_capacity'],
    "INSERT OR IGNORE INTO station_1 (station_id, station_name, recommended_budget_rub, deadline_days, object_id, object_name, optional, equipment_type, required_capacity, capacity_unit, operating_temperature_c, installed_equipment_id, available_capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
insert_data_from_csv(
    'csv_file\suppliers.csv',
    'suppliers',
    ['supplier_id', 'supplier_name', 'delivery_cost_rub', 'delivery_days'],
    "INSERT OR IGNORE INTO suppliers (supplier_id, supplier_name, delivery_cost_rub, delivery_days) VALUES (?, ?, ?, ?)"
)


