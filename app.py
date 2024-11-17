from flask import Flask, render_template, request, jsonify, send_file
from flask_mysqldb import MySQL
from pymongo import MongoClient
import config, json, os

app = Flask(__name__)
app.config.from_object(config.Config)

# Initialize MySQL
mysql = MySQL(app)
selected_database = None


# Initialize MongoDB
mongo_client = MongoClient(app.config['MONGO_URI'])
mongo_db = mongo_client.get_database()
selected_ns_database = None

@app.route('/')
def index():
    return render_template('terminal.html')

@app.route('/command', methods=['POST'])
def handle_command():
    command = request.json.get('command', '').strip().lower()
    response = ""
    global selected_ns_database 
    
    # Process command
    if command == 'help':
        response = "Available commands: help, docs, clear, hello, exit"
    elif command == 'hello':
        response = "Hello! 😊"
    elif command == 'clear':
        response = 'clear'

    # Database Query
    elif command.startswith('make database'):
        db_name = command.split(' ')[2]
        try:
            # Connect to MySQL and create the database
            cursor = mysql.connection.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
            response = f"Database '{db_name}' created successfully."
        except Exception as e:
            response = f"Error: {str(e)}"
        finally:
            cursor.close()
            
            
    elif command.startswith('make ns database'):
        parts = command.split(' ')
        if len(parts) < 4:
            response = "Error: Database and collection names are required. Usage: make ns database <db_name> <collection_name>"
        else:
            db_name = parts[3]
            collection_name = parts[4] if len(parts) > 4 else None

            try:
                # Check if the database already exists
                existing_databases = mongo_client.list_database_names()
                if db_name in existing_databases:
                    db = mongo_client[db_name]
                    if collection_name:
                        # Check if the collection already exists
                        existing_collections = db.list_collection_names()
                        if collection_name in existing_collections:
                            response = f"Error: Collection '{collection_name}' already exists in database '{db_name}'."
                        else:
                            db.create_collection(collection_name)
                            response = f"Collection '{collection_name}' created successfully in existing database '{db_name}'."
                    else:
                        response = f"Error: Database '{db_name}' already exists. No collection specified to create."
                else:
                    # Database does not exist; create it
                    db = mongo_client[db_name]
                    if collection_name:
                        db.create_collection(collection_name)
                        response = f"Database '{db_name}' and collection '{collection_name}' created successfully."
                    else:
                        db["default_collection"].insert_one({"init": "placeholder"})  # Trigger database creation
                        response = f"Database '{db_name}' created successfully."
            except Exception as e:
                response = f"Error in MongoDB operation: {str(e)}"

            
    elif command == 'display databases':
        try:
            # Connect to MySQL and show all databases
            cursor = mysql.connection.cursor()
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            response = "Databases:\n" + "\n".join([db[0] for db in databases])
        except Exception as e:
            response = f"Error: {str(e)}"
        finally:
            cursor.close()
            
            
    elif command == 'display ns databases':
        try:
            # List all databases in MongoDB
            databases = mongo_client.list_database_names()
            response = "Databases:\n" + "\n".join(databases)
        except Exception as e:
            response = f"Error: {str(e)}"

   
    elif command.startswith('remove database'):
        db_name = command.split(' ')[2] if len(command.split()) > 2 else None
        if db_name:
            try:
                cursor = mysql.connection.cursor()
                cursor.execute(f"DROP DATABASE {db_name}")
                response = f"Database '{db_name}' deleted successfully."
            except Exception as e:
                response = f"Error: {str(e)}"
            finally:
                cursor.close()
    
    elif command.startswith('remove ns database'):
        db_name = command.split(' ')[3] if len(command.split()) > 3 else None
        if db_name:
            try:
                # Delete the MongoDB database
                mongo_client.drop_database(db_name)
                response = f"Database '{db_name}' deleted successfully."
            except Exception as e:
                response = f"Error: {str(e)}"

    
    elif command.startswith("choose database"):
        try:
            global selected_database
            # Extract the database name from the command
            db_name = command[len("choose database"):].strip()
            cursor = mysql.connection.cursor()
            cursor.execute(f"USE {db_name}")
            selected_database = db_name
            response = f"Switched to database: {db_name}"
        except Exception as e:
            response = f"Error switching database: {str(e)}"
            
    elif command.startswith("choose ns database"):
        try:
            # Extract the database name from the command
            db_name = command[len("choose ns database"):].strip()

            if not db_name:
                response = "Error: Database name is required."
            else:
                # Check if the database exists
                mongo_db = mongo_client.get_database(db_name)
                if mongo_db.name != db_name:
                    response = f"Error: No database named '{db_name}' exists."
                else:
                    # Set the global variable to the selected database
                    selected_ns_database = db_name
                    response = f"Switched to database: {db_name}"
        except Exception as e:
            response = f"Error switching database: {str(e)}"

    
    # Table Query
    elif command.startswith("make table"):
        if selected_database is None:
            response = "No database selected. Use the 'choose database' command first."
        else:
            try:
                # Extract table schema from the command
                table_definition = command[len("make table"):].strip()
                cursor = mysql.connection.cursor()
                # Use the selected database explicitly
                cursor.execute(f"CREATE TABLE {selected_database}.{table_definition}")
                response = f"Table created successfully in database: {selected_database}"
            except Exception as e:
                response = f"Error creating table: {str(e)}"
    
    elif command.startswith("make collection"):
        if selected_ns_database is None:
            response = "No MongoDB database selected. Use 'choose ns database <dbname>' first."
        else:
            try:
                # Extract the collection name from the command
                collection_name = command[len("make collection"):].strip()

                if not collection_name:
                    response = "Error: Collection name is required."
                else:
                    # Create the collection in the selected MongoDB database
                    db = mongo_client[selected_ns_database]  # Get the selected database
                    db.create_collection(collection_name)  # Create the collection
                    response = f"Collection '{collection_name}' created successfully in database: {selected_ns_database}"
            except Exception as e:
                response = f"Error creating collection: {str(e)}"

           
    elif command.startswith("remove table"):
         if selected_database is None:
             response = "No database selected. Use the 'choose database' command first."
         else:
             try:
                 # Extract the table name from the command
                 table_name = command[len("remove table"):].strip()
                 cursor = mysql.connection.cursor()
                 # Drop the table in the selected database
                 cursor.execute(f"DROP TABLE {selected_database}.{table_name}")
                 response = f"Table '{table_name}' deleted successfully from database: {selected_database}"
             except Exception as e:
                 response = f"Error deleting table: {str(e)}"
  
                 
    elif command.startswith("remove collection"):
        if selected_ns_database is None:
            response = "No MongoDB database selected. Use 'choose ns database <dbname>' first."
        else:
            try:
                # Extract the collection name from the command
                collection_name = command[len("remove collection"):].strip()

                if not collection_name:
                    response = "Error: Collection name is required."
                else:
                    # Get the selected MongoDB database
                    db = mongo_client[selected_ns_database]

                    # Check if the collection exists
                    if collection_name in db.list_collection_names():
                        # Drop the collection
                        db[collection_name].drop()
                        response = f"Collection '{collection_name}' deleted successfully from database: {selected_ns_database}"
                    else:
                        response = f"Error: Collection '{collection_name}' does not exist in database: {selected_ns_database}"
            except Exception as e:
                response = f"Error deleting collection: {str(e)}"

    
    elif command == "display tables":
        if selected_database is None:
            response = "No database selected. Use the 'choose database' command first."
        else:
            try:
                cursor = mysql.connection.cursor()
                # Show tables in the selected database
                cursor.execute(f"SHOW TABLES FROM {selected_database}")
                tables = cursor.fetchall()
                if tables:
                    response = "Tables in database " + selected_database + ":\n" + "\n".join([table[0] for table in tables])
                else:
                    response = f"No tables found in the database: {selected_database}."
            except Exception as e:
                response = f"Error showing tables: {str(e)}"
                
    elif command == "display collections":
        if selected_ns_database is None:
            response = "No MongoDB database selected. Use 'choose ns database <dbname>' first."
        else:
            try:
                # Get the selected database
                db = mongo_client[selected_ns_database]

                # List the collections in the selected MongoDB database
                collections = db.list_collection_names()

                if collections:
                    response = "Collections in database '" + selected_ns_database + "':\n" + "\n".join(collections)
                else:
                    response = f"No collections found in the database: {selected_ns_database}."
            except Exception as e:
                response = f"Error showing collections: {str(e)}"

    
    # Data Query
    elif command.startswith("add into"):
        if selected_database is None:
            response = "No database selected. Use the 'choose database' command first."
        else:
            try:
                # Extract the insert command, preserving case
                insert_command = command[len("add into"):].strip()
                # Format the query assuming 'add into table_name (column1, column2, ...) values (value1, value2, ...)'
                cursor = mysql.connection.cursor()
                cursor.execute(f"INSERT INTO {selected_database}.{insert_command}")
                mysql.connection.commit()  # Commit the transaction
                response = f"Data inserted successfully into table in database: {selected_database}"
            except Exception as e:
                response = f"Error inserting data: {str(e)}"
    
    elif command.startswith("add ns into"):
        if selected_ns_database is None:
            response = "No MongoDB database selected. Use 'choose ns database <dbname>' first."
        else:
            try:
                # Extract the collection name and data from the command
                parts = command[len("add ns into"):].strip().split(" ", 1)
                if len(parts) < 2:
                    response = "Error: Collection name and data are required. Usage: add ns into <collection_name> <json_data>"
                else:
                    collection_name = parts[0]
                    json_data = parts[1]

                    # Parse the JSON data
                    try:
                        data_dict = eval(json_data)  # Convert string to dictionary (ensure valid format)
                        if not isinstance(data_dict, dict):
                            response = "Error: Data must be a valid JSON object."
                        else:
                            # Get the selected MongoDB database and collection
                            db = mongo_client[selected_ns_database]
                            collection = db[collection_name]

                            # Insert the data into the collection
                            collection.insert_one(data_dict)
                            response = f"Data inserted successfully into collection '{collection_name}' in database '{selected_ns_database}'."
                    except Exception as e:
                        response = f"Error parsing JSON data: {str(e)}"
            except Exception as e:
                response = f"Error inserting data into collection: {str(e)}"

                
    elif command.startswith("display from"):
        if selected_database is None:
            response = "No database selected. Use the 'choose database' command first."
        else:
            try:
                # Extract the table and columns from the command
                parts = command[len("display from"):].strip().split(' ')
                table_name = parts[0]  # The first part is the table name
                columns = parts[1:]  # The rest are the columns, if provided

                # Check for a WHERE condition in the query
                condition = None
                if "condition" in parts:
                    where_index = parts.index("condition") + 1
                    condition = " ".join(parts[where_index:])
                    columns = parts[1:where_index-1]  # Remove columns and 'where' from the query

                # Construct the SELECT query
                if columns:
                    # If columns are provided, fetch those specific columns
                    columns_str = ", ".join(columns)
                    query = f"SELECT {columns_str} FROM {selected_database}.{table_name}"
                else:
                    # If no columns are provided, fetch all columns
                    query = f"SELECT * FROM {selected_database}.{table_name}"

                # Add the condition if it exists
                if condition:
                    query += f" WHERE {condition}"

                cursor = mysql.connection.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()

                if rows:
                    # Get column names (headers)
                    column_names = [desc[0] for desc in cursor.description]

                    # Format the response in tabular form
                    response = f"Data from table '{table_name}':\n"
                    response += "| " + " | ".join(column_names) + " |\n"  # Column headers
                    response += "|-" + "-|-".join(["-" * len(col) for col in column_names]) + "-|\n"  # Table divider

                    for row in rows:
                        response += "| " + " | ".join([str(cell) for cell in row]) + " |\n"  # Data rows

                else:
                    response = f"No data found in table: {table_name} with the specified condition."
            except Exception as e:
                response = f"Error fetching data: {str(e)}"
    
    elif command.startswith("display ns from"):
        if selected_ns_database is None:
            response = "No database selected. Use the 'choose ns database' command first."
        else:
            try:
                # Parse the command to extract collection name, fields, and condition
                parts = command[len("display ns from"):].strip().split('condition')
                main_parts = parts[0].strip().split()  # Split collection name and columns
                collection_name = main_parts[0].strip()  # The first part is the collection name
                columns = main_parts[1:]  # Remaining parts are the columns to fetch
                condition = parts[1].strip() if len(parts) > 1 else None  # Condition part

                # Fetch the collection from the selected database
                db = mongo_client[selected_ns_database]
                collection = db[collection_name]

                # Prepare projection for the specified columns
                projection = {col: 1 for col in columns} if columns else None  # Include only the specified columns

                # Prepare the condition for MongoDB query
                condition_dict = {}
                if condition:
                    # Assuming the condition format is like 'field = value'
                    condition_parts = condition.split('=')
                    if len(condition_parts) == 2:
                        field = condition_parts[0].strip()
                        value = condition_parts[1].strip().strip("'")  # Remove extra quotes if present

                        # Check if the value is an integer, and convert accordingly
                        try:
                            value = int(value)  # Try to convert to integer
                        except ValueError:
                            pass  # If it fails, it's treated as a string

                        # Create the condition dictionary
                        condition_dict = {field: value}
                    else:
                        response = "Invalid condition format. Use 'field = value'."
                        return

                # Execute the query with projection and condition
                data = collection.find(condition_dict, projection)

                # Prepare the response
                results = list(data)  # Convert cursor to a list to count and access data
                if results:
                    response = f"Data from collection '{collection_name}'"
                    if columns:
                        response += f" (columns: {', '.join(columns)})"
                    if condition:
                        response += f" condition '{condition}':\n"
                    else:
                        response += ":\n"

                    # Format each document for readability
                    for document in results:
                        response += json.dumps(document, default=str, indent=4) + "\n"
                else:
                    response = f"No data found in collection: {collection_name} with the specified condition."
            except Exception as e:
                response = f"Error fetching data: {str(e)}"


                
    elif command.startswith("remove from"):
        if selected_database is None:
            response = "No database selected. Use the 'choose database' command first."
        else:
            try:
                # Extract the table name and condition from the command
                parts = command[len("remove from"):].strip().split(' ')
                table_name = parts[0]  # The first part is the table name
                condition = None
                if "condition" in parts:
                    where_index = parts.index("condition") + 1
                    condition = " ".join(parts[where_index:])

                if condition:
                    # Construct the DELETE query with the WHERE condition
                    query = f"DELETE FROM {selected_database}.{table_name} WHERE {condition}"
                else:
                    # If no condition, delete all rows from the table
                    query = f"DELETE FROM {selected_database}.{table_name}"

                cursor = mysql.connection.cursor()
                cursor.execute(query)
                mysql.connection.commit()

                # Check how many rows were affected by the query
                if cursor.rowcount > 0:
                    response = f"Data deleted successfully from table '{table_name}'."
                else:
                    response = f"No matching data found to delete from table '{table_name}'."
            except Exception as e:
                response = f"Error deleting data: {str(e)}"

    elif command.startswith("remove ns from"):
        if selected_ns_database is None:
            response = "No database selected. Use the 'choose ns database' command first."
        else:
            try:
                # Extract the collection name and condition from the command
                parts = command[len("remove ns from"):].strip().split(' ')
                collection_name = parts[0]  # The first part is the collection name
                condition = None
                if "condition" in parts:
                    where_index = parts.index("condition") + 1
                    condition = " ".join(parts[where_index:])

                # Fetch the collection from the selected database
                db = mongo_client[selected_ns_database]
                collection = db[collection_name]

                # Prepare the condition for MongoDB query
                if condition:
                    # Assuming the condition format is like 'field = value'
                    # Parse the condition into a MongoDB query format
                    condition_parts = condition.split('=')
                    if len(condition_parts) == 2:
                        field = condition_parts[0].strip()
                        value = condition_parts[1].strip().strip("'")  # Remove extra quotes if present

                        # Check if the value is an integer, and convert accordingly
                        try:
                            value = int(value)  # Try to convert to integer
                        except ValueError:
                            pass  # If it fails, it's treated as a string
                        
                        # Create the condition dictionary
                        condition_dict = {field: value}

                        # Execute the delete operation with the condition
                        result = collection.delete_many(condition_dict)
                    else:
                        response = "Invalid condition format. Use 'field = value'."
                        return
                else:
                    # If no condition is specified, delete all data from the collection
                    result = collection.delete_many({})

                # Prepare the response
                if result.deleted_count > 0:
                    response = f"Data deleted successfully from collection '{collection_name}'."
                else:
                    response = f"No matching data found to delete from collection '{collection_name}'."
            except Exception as e:
                response = f"Error deleting data: {str(e)}"

    
    elif command.startswith("change in"):
        if selected_database is None:
            response = "No database selected. Use the 'choose database' command first."
        else:
            cursor = None  # Initialize cursor to avoid UnboundLocalError
            try:
                # Extract the table name and remaining parts of the command
                parts = command[len("change in"):].strip().split(' ')
                if len(parts) < 3:
                    response = "Invalid command format. Use: CHANGE IN <table> UPDATE <column=value> CONDITION <condition>"
                    return jsonify(response=response)

                table_name = parts[0]  # First part is the table name
                query_parts = " ".join(parts[1:])  # Combine the rest for parsing
                set_clause = ""
                where_clause = ""
                
                # Split into SET and WHERE clauses
                if "update" in query_parts.lower():  # Ensure 'SET' is present
                    set_start = query_parts.lower().index("update") + len("update")
                    if "condition" in query_parts.lower():
                        where_start = query_parts.lower().index("condition")
                        set_clause = query_parts[set_start:where_start].strip()
                        where_clause = query_parts[where_start + len("condition"):].strip()
                    else:
                        set_clause = query_parts[set_start:].strip()
                else:
                    response = "UPDATE clause missing. Use: CHANGE IN <table> UPDATE <column=value> CONDITION <condition>"
                    return jsonify(response=response)

                if not set_clause:
                    response = "No columns to update. Please provide column=value pairs in the UPDATE clause."
                    return jsonify(response=response)

                # Construct the final query
                if where_clause:
                    query = f"UPDATE {selected_database}.{table_name} SET {set_clause} WHERE {where_clause}"
                else:
                    query = f"UPDATE {selected_database}.{table_name} SET {set_clause}"  # Update all rows if no WHERE clause

                # Execute the query
                cursor = mysql.connection.cursor()
                cursor.execute(query)
                mysql.connection.commit()

                # Check affected rows
                if cursor.rowcount > 0:
                    response = f"Data updated successfully in table '{table_name}'."
                else:
                    response = f"No matching data found to update in table '{table_name}'."
            except Exception as e:
                response = f"Error updating data: {str(e)}"
            finally:
                if cursor:
                    cursor.close()  # Close cursor only if it was successfully initialized

    elif command.startswith("change ns in"):
        if selected_ns_database is None:
            response = "No database selected. Use the 'choose ns database' command first."
        else:
            try:
                # Extract the collection name and remaining parts of the command
                parts = command[len("change ns in"):].strip().split(' ')
                if len(parts) < 3:
                    response = "Invalid command format. Use: CHANGE NS  IN <collection> UPDATE <field=value> CONDITION <condition>"
                    return jsonify(response=response)

                collection_name = parts[0]  # First part is the collection name
                query_parts = " ".join(parts[1:])  # Combine the rest for parsing
                set_clause = ""
                where_clause = ""

                # Split into SET and WHERE clauses
                if "update" in query_parts.lower():  # Ensure 'SET' is present
                    set_start = query_parts.lower().index("update") + len("update")
                    if "condition" in query_parts.lower():
                        where_start = query_parts.lower().index("condition")
                        set_clause = query_parts[set_start:where_start].strip()
                        where_clause = query_parts[where_start + len("condition"):].strip()
                    else:
                        set_clause = query_parts[set_start:].strip()
                else:
                    response = "UPDATE clause missing. Use: CHANGE NS IN <collection> UPDATE <field=value> CONDITION <condition>"
                    return jsonify(response=response)

                if not set_clause:
                    response = "No fields to update. Please provide field=value pairs in the UPDATE clause."
                    return jsonify(response=response)

                # Parse the SET clause into a dictionary for MongoDB update
                set_dict = {}
                set_parts = set_clause.split(',')
                for part in set_parts:
                    field_value = part.split('=')
                    if len(field_value) == 2:
                        field = field_value[0].strip()
                        value = field_value[1].strip().strip("'")  # Remove quotes if present

                        # Check if the value is an integer, and convert accordingly
                        try:
                            value = int(value)  # Try to convert to integer
                        except ValueError:
                            pass  # If it fails, it's treated as a string
                        
                        set_dict[field] = value
                    else:
                        response = f"Invalid field=value pair in UPDATE clause: {part}"
                        return jsonify(response=response)

                # Prepare the condition for MongoDB query (WHERE clause)
                condition_dict = {}
                if where_clause:
                    condition_parts = where_clause.split('=')
                    if len(condition_parts) == 2:
                        field = condition_parts[0].strip()
                        value = condition_parts[1].strip().strip("'")  # Remove quotes if present

                        # Check if the value is an integer, and convert accordingly
                        try:
                            value = int(value)  # Try to convert to integer
                        except ValueError:
                            pass  # If it fails, it's treated as a string
                        
                        condition_dict[field] = value
                    else:
                        response = "Invalid condition format in CONDITION clause. Use 'field=value'."
                        return jsonify(response=response)

                # Fetch the collection from the selected database
                db = mongo_client[selected_ns_database]
                collection = db[collection_name]

                # Execute the update operation
                if condition_dict:
                    result = collection.update_many(condition_dict, {"$set": set_dict})
                else:
                    # If no condition is provided, update all documents
                    result = collection.update_many({}, {"$set": set_dict})

                # Prepare the response
                if result.modified_count > 0:
                    response = f"Data updated successfully in collection '{collection_name}'."
                else:
                    response = f"No matching data found to update in collection '{collection_name}'."
            except Exception as e:
                response = f"Error updating data: {str(e)}"

    
    else:
        response = f"Command not recognized: {command}"

    return jsonify(response=response)

if __name__ == '__main__':
    app.run(debug=True)