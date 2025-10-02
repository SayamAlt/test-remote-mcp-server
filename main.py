from fastmcp import FastMCP
import os, aiosqlite, tempfile

# Use temporary directory for database which should be writable
TEMP_DIR = tempfile.gettempdir()

# Define the path to the SQLite database
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")

# Define the path to the categories JSON file
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

print(f"Using database at: {DB_PATH}")

# Create a FastMCP server instance
mcp = FastMCP("Expense Tracker")

def init_db(): # Initialize the database synchronously
    """ Initialize the SQLite database and create the expenses table if it doesn't exist. """
    try:
        import sqlite3
        with sqlite3.connect(DB_PATH) as c:
            c.execute("PRAGMA journal_mode=WAL;") # Enable WAL mode for better concurrency
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )     
            """)
            # Test write access
            c.execute("INSERT OR IGNORE INTO expenses(date, amount, category) VALUES ('2000-01-01', 0, 'test')")
            c.execute("DELETE FROM expenses WHERE category = 'test'")
            print("Database initialized successfully with write access")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise

# Initialize database synchronously at module load
init_db()

@mcp.tool()
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = "") -> dict:
    """ Add a new expense entry to the database. """
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cursor = await c.execute(
                "INSERT INTO expenses (date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
                (date, amount, category, subcategory, note)
            )
            expense_id = cursor.lastrowid
            await c.commit()
            return {"status": "success", "id": expense_id, "message": "Expense added successfully"}
    except Exception as e:
        if "readonly" in str(e).lower():
            return {"status": "error", "message": "Database is in read-only mode. Check file permissions."}
        return {"status": "error", "message": f"Database error: {str(e)}"}

@mcp.tool()
async def list_expenses(start_date: str, end_date: str) -> list[dict]:
    """ List all expense entries from the database within an inclusive date range. """
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cursor = await c.execute("SELECT id, date, amount, category, subcategory, note FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC, id DESC", (start_date, end_date))
            cols = [d[0] for d in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(cols,row)) for row in rows]
    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}
        
@mcp.tool()
async def summarize_expenses_by_category(start_date: str, end_date: str, category: str = "") -> dict:
    """ Summarize total expenses by category within a specified date range. """
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            if category:
                cursor = await c.execute("SELECT category, SUM(amount) as total_amount, COUNT(*) as count FROM expenses WHERE date BETWEEN ? AND ? AND category = ? GROUP BY category ORDER BY total_amount DESC", (start_date, end_date, category))
            else:
                cursor = await c.execute("SELECT category, SUM(amount) as total_amount, COUNT(*) as count FROM expenses WHERE date BETWEEN ? AND ? GROUP BY category ORDER BY total_amount DESC", (start_date, end_date))
            cols = [d[0] for d in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(cols,row)) for row in rows]
    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}
    
@mcp.tool()
async def delete_expense(expense_id: int) -> dict:
    """ Delete an expense entry from the database by its ID. """
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cursor = await c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            await c.commit()
            return {"status": "ok", "deleted": cursor.rowcount}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting expense: {str(e)}"}
    
@mcp.tool()
async def update_expense(expense_id: int, date: str, amount: float, category: str, subcategory: str = "", note: str = "") -> dict:
    """ Update an existing expense entry in the database by its ID. """
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cursor = await c.execute(
                "UPDATE expenses SET date = ?, amount = ?, category = ?, subcategory = ?, note = ? WHERE id = ?",
                (date, amount, category, subcategory, note, expense_id)
            )
            await c.commit()
            return {"status": "ok", "updated": cursor.rowcount}
    except Exception as e:
        return {"status": "error", "message": f"Error updating expense: {str(e)}"}
    
@mcp.resource("expense:///categories", mime_type="application/json")
def get_categories():
    """ Serve the categories JSON file as a resource. """
    try:
        # Provide default categories if file doesn't exist
        default_categories = {
            "categories": [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Travel",
                "Education",
                "Business",
                "Other"
            ]
        }
        try:
            # Read a fresh copy of the categories JSON file each time the resource is requested
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            import json
            return json.dumps(default_categories, indent=2)
    except Exception as e:
        return {"status": "error", "message": f"Error reading categories: {str(e)}"}

# Run the server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)