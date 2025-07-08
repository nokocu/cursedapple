import sqlite3

# connect to your database
conn = sqlite3.connect('patch.db')
cursor = conn.cursor()


try:
    # delete all entries except id=43
    cursor.execute("DELETE FROM patches WHERE id != ?", (43,))

    # commit
    conn.commit()
    print("All entries except id 43 have been deleted from patches table.")


except Exception as e:
    conn.rollback()
    print(f"An error occurred: {e}")


finally:
    cursor.close()
    conn.close()
