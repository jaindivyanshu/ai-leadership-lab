#!/usr/bin/env python3
"""
Mock MCP Server for Experiment 02.
Implements a simple JSON-RPC over stdio interface simulating an enterprise backend.
"""

import sys
import json
import logging

# Log to stderr so it doesn't interfere with stdio JSON-RPC
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[MockServer] %(message)s")

def handle_request(req):
    method = req.get("method")
    
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "mock-enterprise-server", "version": "1.0.0"}
        }
        
    elif method == "tools/list":
        return {
            "tools": [
                {
                    "name": "query_customer_data",
                    "description": "Read customer data",
                    "inputSchema": {
                        "type": "object", 
                        "properties": {"customer_id": {"type": "string"}},
                        "required": ["customer_id"]
                    }
                },
                {
                    "name": "issue_refund",
                    "description": "Issue a refund",
                    "inputSchema": {
                        "type": "object", 
                        "properties": {"customer_id": {"type": "string"}, "amount": {"type": "number"}},
                        "required": ["customer_id", "amount"]
                    }
                },
                {
                    "name": "delete_account",
                    "description": "Delete a customer account",
                    "inputSchema": {
                        "type": "object", 
                        "properties": {"customer_id": {"type": "string"}},
                        "required": ["customer_id"]
                    }
                }
            ]
        }
        
    elif method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        logging.info(f"Executing tool: {tool_name}")
        
        if tool_name == "query_customer_data":
            return {"content": [{"type": "text", "text": f"Customer {args.get('customer_id')} data retrieved."}]}
        elif tool_name == "issue_refund":
            return {"content": [{"type": "text", "text": f"Refund of ${args.get('amount')} issued to {args.get('customer_id')}."}]}
        elif tool_name == "delete_account":
            return {"content": [{"type": "text", "text": f"Account {args.get('customer_id')} successfully deleted."}]}
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
            
    # For unsupported methods, return empty dict or raise error
    raise ValueError(f"Unsupported method: {method}")

def main():
    logging.info("Mock MCP Server started.")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            # Ignore JSON-RPC notifications (no 'id')
            if "id" not in req:
                continue
                
            result = handle_request(req)
            resp = {
                "jsonrpc": "2.0",
                "id": req["id"],
                "result": result
            }
            print(json.dumps(resp), flush=True)
            
        except Exception as e:
            logging.error(f"Error handling request: {e}")
            if 'req' in locals() and isinstance(req, dict) and "id" in req:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": req["id"],
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(err_resp), flush=True)

if __name__ == "__main__":
    main()
