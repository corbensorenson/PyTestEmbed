# PyTestEmbed MCP Integration

PyTestEmbed now includes **Model Context Protocol (MCP)** support, enabling AI agents like **Augment** and **Cline** to seamlessly use PyTestEmbed's testing and documentation capabilities.

## 🤖 What is MCP?

The Model Context Protocol (MCP) is a standardized way for AI agents to interact with external tools and services. With PyTestEmbed's MCP server, AI agents can:

- **Run tests** in real-time
- **Generate test blocks** for functions
- **Generate documentation blocks** 
- **Parse PyTestEmbed files**
- **Validate syntax**
- **Convert standard Python to PyTestEmbed format**

## 🚀 Quick Start

### 1. Start the MCP Server

**From VSCode:**
- Use Command Palette: `PyTestEmbed: Start MCP Server`
- Or click the MCP status indicator in the bottom status bar

**From Command Line:**
```bash
python -m pytestembed.mcp_server --workspace . --mcp-port 3001
```

### 2. Configure Your AI Agent

**For Augment/Cline/Other MCP Clients:**

Add this to your MCP configuration:

```json
{
  "mcpServers": {
    "pytestembed": {
      "command": "python",
      "args": ["-m", "pytestembed.mcp_server"],
      "env": {
        "WORKSPACE": "."
      }
    }
  }
}
```

### 3. Verify Connection

Check the VSCode status bar for:
- `🟢 Live Test: Connected` - Live testing server running
- `🟢 MCP: Connected` - MCP server running and accessible to AI agents

## 🛠️ Available MCP Tools

### Testing Tools
- **`run_tests`** - Execute all tests in a Python file
- **`run_test_at_line`** - Run a specific test at a line number
- **`get_test_results`** - Get current test execution results
- **`get_coverage`** - Get code coverage information

### Generation Tools  
- **`generate_test_block`** - Generate PyTestEmbed test block for a function
- **`generate_doc_block`** - Generate PyTestEmbed documentation block
- **`generate_both_blocks`** - Generate both test and doc blocks together

### Analysis Tools
- **`parse_file`** - Parse Python file and extract PyTestEmbed blocks
- **`validate_syntax`** - Validate PyTestEmbed syntax in a file
- **`convert_to_pytestembed`** - Convert standard Python to PyTestEmbed format

### Information Resources
- **`workspace`** - Get workspace information and Python files
- **`config`** - Get PyTestEmbed configuration settings
- **`test_status`** - Get current test execution status

## 🎯 Example AI Agent Usage

Here's how an AI agent can use PyTestEmbed through MCP:

```python
# AI agent generates a function
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# AI agent calls MCP tool to generate tests
mcp_client.call_tool("generate_test_block", {
    "file_path": "fibonacci.py",
    "line_number": 1,
    "ai_provider": "lmstudio"
})

# Result: PyTestEmbed test block is generated
test:
    calculate_fibonacci(0) == 0: "Base case: fibonacci(0)",
    calculate_fibonacci(1) == 1: "Base case: fibonacci(1)", 
    calculate_fibonacci(5) == 5: "Small fibonacci number",
    calculate_fibonacci(10) == 55: "Larger fibonacci number"

# AI agent can then run the tests
mcp_client.call_tool("run_tests", {
    "file_path": "fibonacci.py"
})
```

## ⚙️ Configuration

### VSCode Settings

Configure PyTestEmbed MCP integration in VSCode settings:

```json
{
    "pytestembed.mcp_server_enabled": true,
    "pytestembed.mcp_server_port": 3001,
    "pytestembed.auto_start_mcp_server": false
}
```

### Tkinter GUI Configuration

Use `pytestembed --config` to open the configuration GUI with MCP settings:

- **Enable MCP Server** - Toggle MCP server functionality
- **MCP Server Port** - Port for MCP server (default: 3001)
- **Auto-start MCP Server** - Start MCP server automatically with VSCode

## 🔧 Advanced Usage

### Custom AI Provider

```python
# Use specific AI provider for generation
mcp_client.call_tool("generate_both_blocks", {
    "file_path": "mycode.py",
    "line_number": 15,
    "ai_provider": "ollama"  # or "lmstudio"
})
```

### Batch Processing

```python
# Parse multiple files
for file_path in python_files:
    result = mcp_client.call_tool("parse_file", {
        "file_path": file_path
    })
    # Process parsed PyTestEmbed blocks
```

### Integration with Live Testing

The MCP server automatically connects to the live testing server, enabling:
- Real-time test execution
- Live test result updates
- Coverage tracking
- Test status monitoring

## 🚨 Troubleshooting

### MCP Server Won't Start
1. Check Python interpreter path in settings
2. Ensure PyTestEmbed is installed: `pip install pytestembed`
3. Verify port 3001 is available
4. Check VSCode Output panel for errors

### AI Agent Can't Connect
1. Verify MCP server is running (check status bar)
2. Check MCP configuration in your AI agent
3. Ensure firewall allows localhost:3001
4. Try restarting both MCP server and AI agent

### Tools Not Working
1. Verify live test server is running (port 8765)
2. Check workspace path is correct
3. Ensure Python files have proper PyTestEmbed syntax
4. Check AI provider configuration

## 📚 Resources

- **PyTestEmbed Documentation**: See `docs/` directory
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Configuration Guide**: Use `pytestembed --config`
- **VSCode Extension**: Search "PyTestEmbed" in VSCode marketplace

## 🎉 Benefits for Agentic Coding

With MCP integration, AI agents can:

✅ **Write better tests** - Generate comprehensive PyTestEmbed test blocks
✅ **Document code automatically** - Create detailed documentation blocks  
✅ **Validate syntax** - Ensure PyTestEmbed format is correct
✅ **Run tests in real-time** - Execute and verify test results immediately
✅ **Convert existing code** - Transform standard Python to PyTestEmbed format
✅ **Monitor coverage** - Track test coverage and identify gaps

This makes PyTestEmbed the perfect companion for agentic coding workflows, enabling AI agents to write, test, and document Python code with unprecedented efficiency and quality.
