#!/usr/bin/env python3
"""
Agentic Harness - Governed MCP Gateway

This script acts as a proxy between an AI agent and an MCP server.
It intercepts 'tools/call' JSON-RPC requests, evaluates them against
a governance policy (policy.yaml), and enforces allow-lists, 
rate-limits, and human-in-the-loop approvals.
"""

import sys
import json
import yaml
import time
import subprocess
import threading
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[Harness] %(message)s")

class GovernanceGateway:
    def __init__(self, policy_path, server_cmd):
        with open(policy_path, 'r') as f:
            self.policy = yaml.safe_load(f)
            
        self.audit_log = self.policy.get("audit_log", "audit.jsonl")
        self.default_action = self.policy.get("default_action", "deny")
        self.tool_policies = self.policy.get("policies", {})
        
        self.rate_limits = {} # tool -> list of timestamps
        
        # Start backend server
        logging.info(f"Starting backend server: {' '.join(server_cmd)}")
        self.process = subprocess.Popen(
            server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
    def log_audit(self, event_type, tool, decision, reason, request_id):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "tool": tool,
            "decision": decision,
            "reason": reason,
            "request_id": request_id
        }
        with open(self.audit_log, 'a') as f:
            f.write(json.dumps(entry) + '\n')
            
    def check_rate_limit(self, tool_name, limit):
        now = time.time()
        # Clean up old timestamps (older than 60 seconds)
        timestamps = self.rate_limits.get(tool_name, [])
        timestamps = [ts for ts in timestamps if now - ts < 60]
        
        if len(timestamps) >= limit:
            return False
            
        timestamps.append(now)
        self.rate_limits[tool_name] = timestamps
        return True
        
    def require_human_approval(self, tool_name, args):
        logging.warning(f"\n--- HUMAN APPROVAL REQUIRED ---")
        logging.warning(f"Tool: {tool_name}")
        logging.warning(f"Args: {json.dumps(args, indent=2)}")
        
        try:
            # Read directly from tty so we don't consume stdin which is used for MCP
            with open('/dev/tty', 'r') as tty:
                logging.warning("Approve this action? (y/N): ")
                answer = tty.readline().strip().lower()
                return answer == 'y'
        except Exception as e:
            logging.error(f"Failed to get human approval (no tty?): {e}")
            return False

    def handle_tool_call(self, req):
        req_id = req.get("id")
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        policy = self.tool_policies.get(tool_name, {"action": self.default_action})
        action = policy.get("action", self.default_action)
        
        # 1. Check Action
        if action == "deny":
            self.log_audit("tool_call", tool_name, "DENIED", "Tool is explicitly denied by policy", req_id)
            return {"error": {"code": -32000, "message": f"Governance Policy: Access to tool '{tool_name}' is denied."}}
            
        # 2. Check Rate Limit
        limit = policy.get("rate_limit_per_minute")
        if limit and not self.check_rate_limit(tool_name, limit):
            self.log_audit("tool_call", tool_name, "DENIED", "Rate limit exceeded", req_id)
            return {"error": {"code": -32000, "message": f"Governance Policy: Rate limit exceeded for '{tool_name}'."}}
            
        # 3. Check Approval
        if action == "require_approval":
            approved = self.require_human_approval(tool_name, args)
            if not approved:
                self.log_audit("tool_call", tool_name, "DENIED", "Human approval rejected or timed out", req_id)
                return {"error": {"code": -32000, "message": f"Governance Policy: Human approval denied for '{tool_name}'."}}
                
        # Allowed!
        self.log_audit("tool_call", tool_name, "ALLOWED", "Policy checks passed", req_id)
        return None # None means forward to backend

    def run(self):
        # Thread to forward backend stdout to our stdout
        def forward_stdout():
            for line in self.process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                
        t = threading.Thread(target=forward_stdout, daemon=True)
        t.start()
        
        # Main loop: read stdin, proxy to backend
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                    
                req = json.loads(line)
                
                # Intercept tool calls
                if req.get("method") == "tools/call":
                    error_resp = self.handle_tool_call(req)
                    if error_resp:
                        # Return error immediately, do not forward
                        resp = {
                            "jsonrpc": "2.0",
                            "id": req.get("id"),
                            "error": error_resp["error"]
                        }
                        print(json.dumps(resp), flush=True)
                        continue
                
                # Forward everything else (and allowed tool calls) to backend
                self.process.stdin.write(line + '\n')
                self.process.stdin.flush()
                
        except KeyboardInterrupt:
            pass
        finally:
            self.process.terminate()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: gateway.py <policy.yaml> <backend_command...>", file=sys.stderr)
        sys.exit(1)
        
    policy_file = sys.argv[1]
    backend_cmd = sys.argv[2:]
    
    gateway = GovernanceGateway(policy_file, backend_cmd)
    gateway.run()
