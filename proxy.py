from fastmcp import FastMCP

# Create a proxy to your remote FastMCP Cloud server instance
# FastMCP Cloud uses Streamable HTTP (default), so just use the URL of your instance
mcp = FastMCP.as_proxy(
    "https://nearby-chocolate-toucan.fastmcp.app/mcp", # Standard FastMCP Cloud URL
    name="Sayam Proxy Server"
)

if __name__ == "__main__":
    # This runs via STDIO, which Claude Desktop can communicate with
    mcp.run()