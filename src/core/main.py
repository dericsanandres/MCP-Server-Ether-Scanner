"""Main entry point for MCP Etherscan server."""

from .server import mcp


def main():
    """Main entry point."""
    mcp.run()


if __name__ == "__main__":
    main()
