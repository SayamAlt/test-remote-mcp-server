from fastmcp import FastMCP
import os, sqlite3, tempfile

# Use temporary directory for database which should be writable
TEMP_DIR = tempfile.gettempdir()

# Define the path to the SQLite database
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")

# Define the path to the categories JSON file
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

print(f"Using database at: {DB_PATH}")

# Create a FastMCP server instance
mcp = FastMCP(name="Expense Tracker")

def init_db():
    """ Initialize the SQLite database and create the expenses table if it doesn't exist. """
    with sqlite3.connect(DB_PATH) as c:
        c.execute('''
             CREATE TABLE IF NOT EXISTS expenses (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 date TEXT NOT NULL,
                 amount REAL NOT NULL,
                 category TEXT NOT NULL,
                 subcategory TEXT DEFAULT '',
                 note TEXT DEFAULT ''
             )     
        ''')

init_db() # Initialize database on startup
@mcp.tool
def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = "") -> str:
    """ Add a new expense entry to the database. """
    with sqlite3.connect(DB_PATH) as c:
        cursor = c.execute(
            "INSERT INTO expenses (date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
            (date, amount, category, subcategory, note)
        )
        return {"status": "ok", "id": str(cursor.lastrowid)}

@mcp.tool
def list_expenses(start_date: str, end_date: str) -> list[dict]:
    """ List all expense entries from the database within a specified date range. """
    with sqlite3.connect(DB_PATH) as c:
        cursor = c.execute("SELECT id, date, amount, category, subcategory, note FROM expenses WHERE date BETWEEN ? AND ? ORDER BY id ASC", (start_date, end_date))
        cols = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(cols,row)) for row in rows]
        
@mcp.tool
def summarize_expenses_by_category(start_date: str, end_date: str, category: str = "") -> dict:
    """ Summarize total expenses by category within a specified date range. """
    with sqlite3.connect(DB_PATH) as c:
        if category:
            cursor = c.execute("SELECT category, SUM(amount) as total FROM expenses WHERE date BETWEEN ? AND ? AND category = ? GROUP BY category ORDER BY category ASC", (start_date, end_date, category))
        else:
            cursor = c.execute("SELECT category, SUM(amount) as total FROM expenses WHERE date BETWEEN ? AND ? GROUP BY category ORDER BY category ASC", (start_date, end_date))
        cols = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(cols,row)) for row in rows]
 
@mcp.tool
def delete_expense(expense_id: int) -> dict:
    """ Delete an expense entry from the database by its ID. """
    with sqlite3.connect(DB_PATH) as c:
        cursor = c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        c.commit()
        return {"status": "ok", "deleted": cursor.rowcount}
    
@mcp.tool
def update_expense(expense_id: int, date: str, amount: float, category: str, subcategory: str = "", note: str = "") -> dict:
    """ Update an existing expense entry in the database by its ID. """
    with sqlite3.connect(DB_PATH) as c:
        cursor = c.execute(
            "UPDATE expenses SET date = ?, amount = ?, category = ?, subcategory = ?, note = ? WHERE id = ?",
            (date, amount, category, subcategory, note, expense_id)
        )
        c.commit()
        return {"status": "ok", "updated": cursor.rowcount}
    
@mcp.resource("expense://categories", mime_type="application/json")
def get_categories():
    # Read a fresh copy of the categories JSON file each time the resource is requested
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

# Run the server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)