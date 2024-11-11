import sqlite3

# Connect to your database (replace 'database.db' with your database name)
conn = sqlite3.connect('patch.db')
cursor = conn.cursor()

try:
    # Delete all entries except the one with id=43
    cursor.execute("DELETE FROM patches WHERE id != ?", (43,))

    # Commit the transaction
    conn.commit()
    print("All entries except id 43 have been deleted from patches table.")

except Exception as e:
    # Rollback in case of any error
    conn.rollback()
    print(f"An error occurred: {e}")

finally:
    # Close the connection
    cursor.close()
    conn.close()
