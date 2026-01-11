#!/usr/bin/env python3
"""
Modern MCP Client - Web Interface with Modern Minimal Brutalist Design
Full MCP protocol support with SSE handling for tool discovery and execution
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import httpx
import uvicorn
from contextlib import asynccontextmanager
import json
import re

# MCP Server Configuration
MCP_ENDPOINT = "https://openehr-mcp.fastmcp.app/mcp"

# Global state
mcp_tools = []
mcp_resources = []
mcp_prompts = []

def parse_sse_response(text: str) -> Optional[Dict]:
    """Parse Server-Sent Events response to extract JSON-RPC data"""
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('data: '):
            data_part = line[6:].strip()
            if data_part and data_part != '[DONE]':
                try:
                    return json.loads(data_part)
                except json.JSONDecodeError:
                    continue
    return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MCP connection with SSE support"""
    global mcp_tools, mcp_resources, mcp_prompts
    
    print("🚀 Connecting to MCP Server...")
    print(f"📍 {MCP_ENDPOINT}")
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Get tools with SSE handling
            tools_resp = await client.post(
                MCP_ENDPOINT, 
                json={
                    "jsonrpc": "2.0", 
                    "id": 1, 
                    "method": "tools/list",
                    "params": {}
                },
                headers=headers
            )
            
            if tools_resp.status_code == 200:
                # Try to parse as SSE first
                response_text = tools_resp.text
                data = parse_sse_response(response_text)
                
                # If SSE parsing failed, try direct JSON
                if not data:
                    try:
                        data = tools_resp.json()
                    except:
                        data = None
                
                if data and "result" in data and "tools" in data["result"]:
                    mcp_tools = data["result"]["tools"]
                    print(f"✅ {len(mcp_tools)} tools loaded")
                    for tool in mcp_tools[:5]:
                        print(f"   • {tool.get('name', 'unknown')}")
                else:
                    print(f"⚠️  No tools found in response")
                    print(f"   Response preview: {response_text[:200]}")
            else:
                print(f"⚠️ HTTP {tools_resp.status_code}")
                    
    except Exception as e:
        print(f"⚠️  Connection failed: {e}")
        import traceback
        traceback.print_exc()
    
    yield
    print("👋 Shutdown")

app = FastAPI(title="MCP Client", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

@app.get("/", response_class=HTMLResponse)
async def root():
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenEHR MCP Client 🏥</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* Modern Minimal Brutalist Design System */
        :root {
            /* Primary - Vibrant Green */
            --color-primary: #22c55e;
            --color-primary-dark: #16a34a;
            --color-primary-light: #4ade80;

            /* Accent - Pure Black */
            --color-accent: #000000;
            --color-accent-dark: #1a1a1a;

            /* Semantic */
            --color-success: #22c55e;
            --color-error: #ef4444;
            --color-danger-dark: #dc2626;

            /* Neutrals */
            --color-background: #ffffff;
            --color-text-primary: #000000;
            --color-text-secondary: #404040;
            --color-text-muted: #737373;
            --color-border: #e5e5e5;

            /* Shadows */
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
            --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
            --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(to bottom, #fafafa, #f5f5f5);
            color: var(--color-text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            min-height: 100vh;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1.2;
        }
        
        .container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 0 1.5rem;
        }
        
        /* Hero Section */
        .hero {
            background: #ffffff;
            border: 2px solid #000000;
            border-radius: 12px;
            padding: 3rem 2rem;
            margin: 2rem 0;
            text-align: center;
        }
        
        .icon-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 6rem;
            height: 6rem;
            border-radius: 8px;
            font-size: 3.75rem;
            border: 2px solid var(--color-border);
            background: linear-gradient(145deg, #ffffff, #f8f8f8);
            box-shadow: 
                0 2px 4px rgba(0, 0, 0, 0.05),
                inset 0 1px 0 rgba(255, 255, 255, 0.3);
            transition: all 0.2s ease;
            margin-bottom: 1.5rem;
        }
        
        .icon-badge:hover {
            border-color: var(--color-primary);
            transform: translateY(-2px);
            box-shadow: 
                0 4px 6px rgba(34, 197, 94, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.4);
        }
        
        .hero h1 {
            font-size: 3rem;
            margin-bottom: 0.75rem;
            color: var(--color-text-primary);
        }
        
        .hero .subtitle {
            font-size: 1.125rem;
            color: var(--color-text-secondary);
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .hero .description {
            font-size: 0.875rem;
            color: var(--color-text-muted);
            font-weight: 500;
        }
        
        /* Card Component */
        .card {
            background: linear-gradient(145deg, #ffffff, #fafafa);
            border-radius: 12px;
            border: 1px solid var(--color-border);
            box-shadow: 
                0 4px 6px -1px rgba(0, 0, 0, 0.1),
                0 2px 4px -1px rgba(0, 0, 0, 0.06),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
            padding: 1.5rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(
                135deg,
                transparent,
                transparent 2px,
                rgba(0, 0, 0, 0.008) 2px,
                rgba(0, 0, 0, 0.008) 4px
            );
            pointer-events: none;
            border-radius: inherit;
        }
        
        .card:hover {
            border-color: var(--color-primary);
            box-shadow: 
                0 10px 15px -3px rgba(34, 197, 94, 0.2),
                0 4px 6px -2px rgba(34, 197, 94, 0.15);
            transform: translateY(-4px);
        }
        
        /* Grid Layout */
        .main-grid {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 2rem;
            margin: 2rem 0;
        }
        
        /* Tools Sidebar */
        .tools-sidebar {
            position: sticky;
            top: 2rem;
            height: fit-content;
        }
        
        .tools-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        
        .tools-header .icon-badge {
            width: 3rem;
            height: 3rem;
            font-size: 1.5rem;
            margin: 0;
        }
        
        .tools-header h2 {
            font-size: 1.25rem;
            color: var(--color-text-primary);
        }
        
        .tools-count {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.25rem 0.625rem;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 6px;
            background: var(--color-primary);
            color: white;
            margin-left: auto;
        }
        
        .tool-item {
            padding: 1rem;
            margin-bottom: 0.5rem;
            background: #ffffff;
            border: 1px solid var(--color-border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
        }
        
        .tool-item:hover {
            border-color: var(--color-primary);
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(34, 197, 94, 0.1);
        }
        
        .tool-name {
            font-weight: 600;
            font-size: 0.9375rem;
            color: var(--color-text-primary);
            margin-bottom: 0.25rem;
        }
        
        .tool-desc {
            font-size: 0.8125rem;
            color: var(--color-text-muted);
            line-height: 1.4;
        }
        
        /* Chat Container */
        .chat-container {
            display: flex;
            flex-direction: column;
            min-height: 600px;
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 1.5rem;
            max-height: 65vh;
        }
        
        .message {
            margin-bottom: 1.5rem;
            padding: 1.25rem;
            border-radius: 8px;
            border-left: 3px solid;
        }
        
        .message.user {
            border-left-color: #000000;
            background: #f5f5f5;
        }
        
        .message.assistant {
            border-left-color: var(--color-primary);
            background: rgba(34, 197, 94, 0.05);
        }
        
        .message.error {
            border-left-color: var(--color-error);
            background: rgba(239, 68, 68, 0.05);
        }
        
        .message-header {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--color-text-muted);
            margin-bottom: 0.5rem;
            font-weight: 700;
        }
        
        .message-content {
            font-size: 0.9375rem;
            line-height: 1.6;
            color: var(--color-text-primary);
        }
        
        /* Input Area */
        .input-area {
            border-top: 2px solid var(--color-border);
            padding: 1.5rem;
            background: #ffffff;
            border-radius: 0 0 12px 12px;
        }
        
        .search-bar {
            display: flex;
            gap: 1rem;
        }
        
        .search-input {
            flex: 1;
            padding: 0.75rem 1rem;
            border: 1px solid var(--color-border);
            border-radius: 8px;
            font-size: 0.9375rem;
            background: white;
            color: var(--color-text-primary);
            transition: all 0.2s;
            font-family: 'Inter', sans-serif;
        }
        
        .search-input:focus {
            outline: none;
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.1);
        }
        
        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-size: 0.9375rem;
            border-radius: 8px;
            border: 2px solid transparent;
            transition: all 0.2s ease;
            cursor: pointer;
            white-space: nowrap;
            font-family: 'Inter', sans-serif;
        }
        
        .btn-primary {
            background: var(--color-primary);
            color: white;
            border-color: var(--color-primary);
        }
        
        .btn-primary:hover {
            background: var(--color-primary-dark);
            border-color: var(--color-primary-dark);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        /* Code Block */
        .code-block {
            background: #000000;
            color: var(--color-primary);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            overflow-x: auto;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.875rem;
            border: 1px solid var(--color-border);
        }
        
        /* Loading State */
        .loading {
            display: none;
            text-align: center;
            padding: 1.5rem;
            color: var(--color-primary);
            font-weight: 600;
        }
        
        .loading.active {
            display: block;
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        
        /* Status Bar */
        .status-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #ffffff;
            border-top: 1px solid var(--color-border);
            padding: 0.75rem 1.5rem;
            font-size: 0.875rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.05);
            z-index: 100;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--color-text-secondary);
            font-weight: 500;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--color-primary);
            animation: pulse-dot 2s ease-in-out infinite;
        }
        
        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }
        
        .tool-count-badge {
            background: var(--color-accent);
            color: white;
            padding: 0.375rem 0.75rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.8125rem;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
            
            .tools-sidebar {
                position: static;
            }
            
            .hero {
                padding: 2rem 1.5rem;
            }
            
            .hero h1 {
                font-size: 2rem;
            }
            
            .icon-badge {
                width: 4rem;
                height: 4rem;
                font-size: 2.5rem;
            }
            
            .status-bar {
                flex-direction: column;
                gap: 0.5rem;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Hero Section -->
        <div class="hero">
            <div class="icon-badge">🏥</div>
            <h1>OpenEHR MCP Client</h1>
            <p class="subtitle">Medical Coding Protocol Interface</p>
            <p class="description">Semantic ICD-10 search, EHR queries, and clinical data management</p>
        </div>
        
        <div class="main-grid">
            <!-- Tools Sidebar -->
            <div class="tools-sidebar">
                <div class="card">
                    <div class="tools-header">
                        <div class="icon-badge">🔧</div>
                        <h2>Tools</h2>
                        <span class="tools-count" id="tools-count">0</span>
                    </div>
                    <div id="tools-list"></div>
                </div>
            </div>
            
            <!-- Main Chat Area -->
            <div class="card" style="padding: 0;">
                <div class="chat-container">
                    <div class="messages" id="messages">
                        <div class="message assistant">
                            <div class="message-header">✨ WELCOME</div>
                            <div class="message-content">
                                <strong>Ready to help!</strong> I can search ICD-10 codes, query EHRs, and manage clinical data. 
                                Try searching for "cholera" or "diabetes" to get started. 🎯
                            </div>
                        </div>
                    </div>
                    <div class="loading" id="loading">⚡ Processing your request...</div>
                    <div class="input-area">
                        <div class="search-bar">
                            <input 
                                type="text" 
                                class="search-input" 
                                id="query-input"
                                placeholder="Search for medical codes, conditions, or ask a question..."
                            >
                            <button class="btn btn-primary" onclick="sendQuery()">Search 🔍</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Status Bar -->
    <div class="status-bar">
        <div class="status-indicator">
            <div class="status-dot"></div>
            <span>Connected to MCP Server</span>
        </div>
        <div class="tool-count-badge" id="status-tool-count">0 tools</div>
    </div>

    <script>
        let tools = [];
        let messageId = 1;

        // Load tools on page load
        async function loadTools() {
            try {
                const response = await fetch('/api/tools');
                const data = await response.json();
                tools = data.tools || [];
                
                const count = tools.length;
                document.getElementById('tools-count').textContent = count;
                document.getElementById('status-tool-count').textContent = `${count} tool${count !== 1 ? 's' : ''}`;
                
                const toolsList = document.getElementById('tools-list');
                
                if (count === 0) {
                    toolsList.innerHTML = '<div class="tool-desc" style="padding: 1rem; text-align: center;">⏳ Loading tools...</div>';
                } else {
                    toolsList.innerHTML = tools.map(tool => `
                        <div class="tool-item" onclick="selectTool('${tool.name}')">
                            <div class="tool-name">${tool.name}</div>
                            <div class="tool-desc">${truncate(tool.description || '', 70)}</div>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Failed to load tools:', error);
                addMessage('error', 'Failed to load MCP tools. Check connection.');
            }
        }

        function truncate(text, length) {
            return text.length > length ? text.substring(0, length) + '...' : text;
        }

        function selectTool(toolName) {
            const tool = tools.find(t => t.name === toolName);
            if (!tool) return;
            
            addMessage('user', `Selected tool: <strong>${toolName}</strong>`);
            
            // Create example query based on tool
            const exampleQueries = {
                'suggest_icd_codes': 'cholera',
                'search_icd_code': 'A00',
                'query_ehr': 'SELECT * FROM EHR LIMIT 5',
                'list_ehrs': 'show all EHRs',
                'get_composition': 'patient data'
            };
            
            const example = exampleQueries[toolName] || `Use ${toolName}`;
            document.getElementById('query-input').value = example;
            document.getElementById('query-input').focus();
        }

        async function sendQuery() {
            const input = document.getElementById('query-input');
            const query = input.value.trim();
            
            if (!query) return;
            
            addMessage('user', query);
            input.value = '';
            
            const loading = document.getElementById('loading');
            loading.classList.add('active');
            
            try {
                // Smart tool detection
                let toolName = 'suggest_icd_codes';
                let args = { clinical_text: query, limit: 5 };
                
                // Detect tool from query
                if (query.toLowerCase().startsWith('select') || query.toLowerCase().includes('query')) {
                    toolName = 'query_ehr';
                    args = { aql_query: query };
                } else if (query.toLowerCase().includes('list ehr') || query.toLowerCase().includes('show ehr')) {
                    toolName = 'list_ehrs';
                    args = {};
                } else if (/^[A-Z]\d{2}/.test(query)) {
                    // Looks like an ICD code
                    toolName = 'search_icd_code';
                    args = { code: query };
                }
                
                // Check if tool exists
                const tool = tools.find(t => t.name === toolName);
                if (!tool) {
                    addMessage('error', `Tool "${toolName}" not found. Available tools: ${tools.map(t => t.name).join(', ')}`);
                    loading.classList.remove('active');
                    return;
                }
                
                const response = await fetch('/api/tools/call', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tool_name: toolName,
                        arguments: args
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    addMessage('error', data.error);
                } else {
                    addMessage('assistant', formatResponse(data.result, toolName));
                }
            } catch (error) {
                addMessage('error', `Network error: ${error.message}`);
            } finally {
                loading.classList.remove('active');
            }
        }

        function formatResponse(result, toolName) {
            if (typeof result === 'string') {
                // Check if it's JSON string
                try {
                    const parsed = JSON.parse(result);
                    return formatJSON(parsed);
                } catch {
                    return result;
                }
            }
            return formatJSON(result);
        }

        function formatJSON(data) {
            if (Array.isArray(data)) {
                if (data.length === 0) return '<em>No results found</em>';
                
                // Format ICD codes nicely
                if (data[0] && data[0].code && data[0].description) {
                    let html = '<div style="margin-top: 0.5rem;">';
                    data.forEach((item, idx) => {
                        const score = item.score ? ` <span style="color: var(--color-primary); font-weight: 600;">(${(item.score * 100).toFixed(1)}%)</span>` : '';
                        html += `<div style="padding: 0.75rem; background: #f9f9f9; border-left: 3px solid var(--color-primary); margin-bottom: 0.5rem; border-radius: 4px;">
                            <strong>${item.code}</strong>${score}<br>
                            <span style="color: var(--color-text-secondary);">${item.description}</span>
                        </div>`;
                    });
                    html += '</div>';
                    return html;
                }
            }
            
            return `<div class="code-block">${JSON.stringify(data, null, 2)}</div>`;
        }

        function addMessage(type, content) {
            const messages = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            const headers = {
                'user': '👤 YOU',
                'error': '❌ ERROR',
                'assistant': '✅ MCP RESPONSE'
            };
            
            messageDiv.innerHTML = `
                <div class="message-header">${headers[type] || 'MESSAGE'}</div>
                <div class="message-content">${content}</div>
            `;
            
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }

        // Enter key support
        document.getElementById('query-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendQuery();
            }
        });

        // Load tools on startup
        loadTools();
        
        // Refresh tools every 10 seconds
        setInterval(loadTools, 10000);
    </script>
</body>
</html>
    """


@app.get("/api/tools")
async def get_tools():
    """Get available MCP tools"""
    return {"tools": mcp_tools, "resources": mcp_resources, "prompts": mcp_prompts}


@app.post("/api/tools/call")
async def call_tool(request: ToolCallRequest):
    """Execute an MCP tool with SSE support"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.post(
                MCP_ENDPOINT,
                json={
                    "jsonrpc": "2.0",
                    "id": 100,
                    "method": "tools/call",
                    "params": {
                        "name": request.tool_name,
                        "arguments": request.arguments
                    }
                },
                headers=headers
            )
            
            if response.status_code == 200:
                # Try SSE parsing first
                response_text = response.text
                data = parse_sse_response(response_text)
                
                # If SSE parsing failed, try direct JSON
                if not data:
                    try:
                        data = response.json()
                    except:
                        return {"error": f"Failed to parse response: {response_text[:200]}"}
                
                if "error" in data:
                    return {"error": data["error"].get("message", "Unknown error")}
                
                if "result" in data:
                    result = data["result"]
                    
                    # Extract text from content if present
                    if isinstance(result, dict) and "content" in result:
                        content_items = result["content"]
                        if isinstance(content_items, list) and len(content_items) > 0:
                            text_content = ""
                            for item in content_items:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    text_content += item.get("text", "")
                            return {"result": text_content if text_content else result}
                    
                    return {"result": result}
            
            return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Tool call error: {error_detail}")
        return {"error": str(e)}


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "mcp_endpoint": MCP_ENDPOINT,
        "tools_loaded": len(mcp_tools)
    }


if __name__ == "__main__":
    print("🚀 Starting MCP Client Web Server...")
    print("📍 http://localhost:8000")
    print(f"🔗 MCP Endpoint: {MCP_ENDPOINT}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
