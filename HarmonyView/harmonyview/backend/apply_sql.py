import pyodbc
import os

def run_sql_file(file_path):
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.environ['DB_HOST']},{os.environ['DB_PORT']};"
        f"DATABASE={os.environ['DB_DATABASE']};"
        f"UID={os.environ['DB_USERNAME']};"
        f"PWD={os.environ['DB_PASSWORD']};"
        "TrustServerCertificate=yes;"
    )
    
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()
        
    # Split by GO
    parts = sql.split('GO')
    for part in parts:
        if part.strip():
            try:
                cursor.execute(part)
            except Exception as e:
                print(f"Error executing part: {e}")
                
    conn.close()
    print("SQL execution completed.")

if __name__ == "__main__":
    run_sql_file('/home/sua_it_ai/controltower/harmonyview/backend/sql/views_duration_analysis.sql')
