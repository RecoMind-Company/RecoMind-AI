# embedding/database_scanner.py

import pyodbc
from collections import defaultdict
# We no longer need to import the global config file here

class DatabaseScanner:
    """
    Connects to the source SQL Server database to fetch schemas,
    primary keys, and foreign key relationships for all tables.
    """
    def __init__(self, db_settings: dict):
        """Initializes the database connection string from the passed settings dictionary."""
        if not all(k in db_settings for k in ['server', 'database', 'username', 'password']):
             raise ValueError("The provided db_settings dictionary is missing one or more required keys.")
        
        try:
            self.conn_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={db_settings['server']};DATABASE={db_settings['database']};"
                f"UID={db_settings['username']};PWD={db_settings['password']}"
            )
        except Exception as e:
            raise ValueError(f"Error building connection string: {e}")

    # ... The rest of the file (_execute_query, _fetch_primary_keys, etc.) remains exactly the same ...
    def _execute_query(self, cursor, query: str) -> list:
        # ... (no change)
        cursor.execute(query)
        return cursor.fetchall()

    def _fetch_primary_keys(self, cursor) -> dict:
        # ... (no change)
        query = """
        SELECT s.name AS schema_name, t.name AS table_name, c.name AS column_name
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        INNER JOIN sys.indexes i ON t.object_id = i.object_id
        INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND c.column_id = ic.column_id
        WHERE i.is_primary_key = 1;
        """
        primary_keys = {}
        for row in self._execute_query(cursor, query):
            full_table_name = f"{row.schema_name}.{row.table_name}"
            primary_keys[full_table_name] = row.column_name
        print(f"Successfully fetched {len(primary_keys)} primary keys.")
        return primary_keys

    def _fetch_foreign_key_relationships(self, cursor) -> dict:
        # ... (no change)
        query = """
        SELECT
            fk.name AS constraint_name,
            OBJECT_SCHEMA_NAME(fk.parent_object_id) AS from_schema,
            OBJECT_NAME(fk.parent_object_id) AS from_table,
            c1.name AS from_column,
            OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS to_schema,
            OBJECT_NAME(fk.referenced_object_id) AS to_table,
            c2.name AS to_column
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.columns AS c1 ON fkc.parent_object_id = c1.object_id AND fkc.parent_column_id = c1.column_id
        INNER JOIN sys.columns AS c2 ON fkc.referenced_object_id = c2.object_id AND fkc.referenced_column_id = c2.column_id;
        """
        relationships = defaultdict(list)
        for row in self._execute_query(cursor, query):
            from_table_full = f"{row.from_schema}.{row.from_table}"
            to_table_full = f"{row.to_schema}.{row.to_table}"
            relationships[from_table_full].append({
                "from_column": row.from_column,
                "to_table": to_table_full,
                "to_column": row.to_column
            })
        print(f"Successfully fetched {sum(len(v) for v in relationships.values())} foreign key relationships.")
        return dict(relationships)

    def scan_tables(self) -> list:
        # ... (no change)
        table_schema_details = []
        try:
            with pyodbc.connect(self.conn_string) as cnxn:
                cursor = cnxn.cursor()
                
                all_pks = self._fetch_primary_keys(cursor)
                all_fks = self._fetch_foreign_key_relationships(cursor)
                
                table_list_query = "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
                all_tables_meta = self._execute_query(cursor, table_list_query)
                print(f"Found {len(all_tables_meta)} tables to process.")
                
                for table_schema, table_name in all_tables_meta:
                    full_table_name = f"{table_schema}.{table_name}"
                    
                    schema_query = "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?"
                    cursor.execute(schema_query, table_schema, table_name)
                    
                    schema_details_text = "\n".join([f"{col[0]} ({col[1]}, Nullable: {col[2]})" for col in cursor.fetchall()])
                    
                    key_info = {
                        "pk": all_pks.get(full_table_name),
                        "fks": all_fks.get(full_table_name, [])
                    }
                    
                    table_schema_details.append({
                        'full_name': full_table_name,
                        'schema_text': schema_details_text,
                        'key_info': key_info 
                    })
            
            return table_schema_details

        except Exception as e:
            print(f"\nFATAL ERROR: Could not connect or fetch from source DB: {e}")
            import traceback
            traceback.print_exc()
            return []