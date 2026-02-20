"""
Run migration 017: Add ASNSent and IrsaliyeSent flags to DollySubmissionHold
"""
import pyodbc
import sys

# Database connection
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=dollydb_test;"
    "UID=sa;"
    "PWD=YourStrong@Passw0rd;"
    "TrustServerCertificate=yes;"
)

try:
    print("🔌 Connecting to database...")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Check if ASNSent column exists
    print("\n📋 Checking existing columns...")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sys.columns 
        WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
        AND name = 'ASNSent'
    """)
    asn_exists = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sys.columns 
        WHERE object_id = OBJECT_ID('dbo.DollySubmissionHold') 
        AND name = 'IrsaliyeSent'
    """)
    irsaliye_exists = cursor.fetchone()[0]
    
    # Add ASNSent column if not exists
    if not asn_exists:
        print("\n➕ Adding ASNSent column...")
        cursor.execute("""
            ALTER TABLE dbo.DollySubmissionHold 
            ADD ASNSent BIT NOT NULL DEFAULT 0
        """)
        conn.commit()
        print("✅ ASNSent column added successfully")
    else:
        print("ℹ️  ASNSent column already exists")
    
    # Add IrsaliyeSent column if not exists
    if not irsaliye_exists:
        print("\n➕ Adding IrsaliyeSent column...")
        cursor.execute("""
            ALTER TABLE dbo.DollySubmissionHold 
            ADD IrsaliyeSent BIT NOT NULL DEFAULT 0
        """)
        conn.commit()
        print("✅ IrsaliyeSent column added successfully")
    else:
        print("ℹ️  IrsaliyeSent column already exists")
    
    # Verify columns
    print("\n🔍 Verifying migration...")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DollySubmissionHold'
        AND COLUMN_NAME IN ('ASNSent', 'IrsaliyeSent')
        ORDER BY COLUMN_NAME
    """)
    
    print("\n📊 Migration results:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}, Nullable={row[2]}, Default={row[3]}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Migration 017 completed successfully!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
