from fastmcp import FastMCP
import random, json

# Create the FastMCP server instance
mcp = FastMCP("Simple Calculator Server")

# Tool: Add two numbers
@mcp.tool
def add(a: int, b: int) -> int:
    """
        Add two numbers and return the result.
        
        Args:
            a (int): The first number.
            b (int): The second number.
    """
    return a + b

# Tool: Generate a random number within a specified range
@mcp.tool
def random_number(min_val: int = 1, max_val: int = 100) -> int:
    """
        Generate a random number within a specified range.
        
        Args:
            min_val (int): The minimum value of the range (inclusive).
            max_val (int): The maximum value of the range (inclusive).
        
        Returns:
            A random integer between min_val and max_val.
    """
    return random.randint(min_val, max_val)

# Resource: Server information
@mcp.resource("info://server")
def server_info() -> str:
    """
        Get information about the server.
    """
    info = {
        "name": "Simple Calculator Server",
        "version": "1.0.0",
        "description": "A basic MCP server with math tools.",
        "tools": ["add", "random_number"],
        "author": "Sayam Kumar"
    }
    return json.dumps(info, indent=2)

# Run the server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)