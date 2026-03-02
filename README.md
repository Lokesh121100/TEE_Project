# TEE Service Desk AI Automation

This project implements an AI-powered IT Service Desk automation solution for the Technical Evaluation Exercise (TEE).

## Project Structure

```text
├── docs/                   # Project documentation & status reports
│   └── requirements/       # Original tender requirement documents
├── mcp/                    # Model Context Protocol (MCP) integrations
│   └── servicenow/         # ServiceNow MCP server & configuration
├── src/                    # Source code
│   └── ai_agent/           # Core AI logic (Hugging Face / Python)
├── scripts/                # Utility & deployment scripts
├── .gitignore              # Sensitive file protection
└── README.md               # Project overview
```

## Quick Start

1.  **AI Virtual Agent**: Run `python src/ai_agent/main.py`
2.  **ServiceNow Integration**: Run `python mcp/servicenow/sn_mcp_tools.py`
3.  **Deployment**: Run `python scripts/deploy_business_rule.py`

## Features

- **Cost-Effective AI**: Uses open-source Hugging Face models.
- **Real-Time Integration**: Seamless connection to ServiceNow via REST APIs.
- **Platform-Side Automation**: Built-in Business Rules for automated ticket routing.
- **TEE Aligned**: Implements mandatory scenarios and transformation roadmaps.