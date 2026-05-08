<div align="center">

# Insurance Verification MCP

**MCP server for insurance verification mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-insurance-verification-mcp)](https://pypi.org/project/meok-insurance-verification-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Insurance Verification MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `verify_eligibility` | Verify patient insurance eligibility with coverage details, copay, deductible, a |
| `prior_authorization_check` | Check if a treatment requires prior authorization with estimated approval timeli |
| `claim_status` | Check insurance claim status with processing stage, payment details, and timelin |
| `fraud_indicators` | Analyze a claim for fraud indicators with risk scoring, pattern detection, and r |

## Installation

```bash
pip install meok-insurance-verification-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "insurance-verification": {
      "command": "python",
      "args": ["-m", "meok_insurance_verification_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 4 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
