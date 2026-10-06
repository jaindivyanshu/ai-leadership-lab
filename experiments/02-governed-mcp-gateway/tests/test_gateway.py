import unittest
import os
import json
from unittest.mock import patch
from gateway import GovernanceGateway

class TestGateway(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary policy file
        cls.policy_path = "test_policy.yaml"
        with open(cls.policy_path, "w") as f:
            f.write("""
audit_log: "test_audit.jsonl"
default_action: "deny"
policies:
  query_customer:
    action: "allow"
    rate_limit_per_minute: 2
  refund:
    action: "require_approval"
  delete_db:
    action: "deny"
""")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.policy_path):
            os.remove(cls.policy_path)
        if os.path.exists("test_audit.jsonl"):
            os.remove("test_audit.jsonl")

    @patch('subprocess.Popen')
    def setUp(self, mock_popen):
        self.gateway = GovernanceGateway(self.policy_path, ["dummy"])
        if os.path.exists("test_audit.jsonl"):
            os.remove("test_audit.jsonl")

    def test_allow_and_rate_limit(self):
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "query_customer", "arguments": {}}
        }
        
        # Call 1: Allowed
        res = self.gateway.handle_tool_call(req)
        self.assertIsNone(res) # None means forward
        
        # Call 2: Allowed
        res = self.gateway.handle_tool_call(req)
        self.assertIsNone(res)
        
        # Call 3: Rate limited
        res = self.gateway.handle_tool_call(req)
        self.assertIsNotNone(res)
        self.assertIn("Rate limit exceeded", res["error"]["message"])

    def test_deny(self):
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "delete_db", "arguments": {}}
        }
        res = self.gateway.handle_tool_call(req)
        self.assertIsNotNone(res)
        self.assertIn("is denied", res["error"]["message"])

    @patch('gateway.GovernanceGateway.require_human_approval')
    def test_require_approval_granted(self, mock_approve):
        mock_approve.return_value = True
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "refund", "arguments": {}}
        }
        res = self.gateway.handle_tool_call(req)
        self.assertIsNone(res) # forwarded

    @patch('gateway.GovernanceGateway.require_human_approval')
    def test_require_approval_denied(self, mock_approve):
        mock_approve.return_value = False
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "refund", "arguments": {}}
        }
        res = self.gateway.handle_tool_call(req)
        self.assertIsNotNone(res)
        self.assertIn("Human approval denied", res["error"]["message"])

    def test_audit_log_written(self):
        req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "delete_db", "arguments": {}}
        }
        self.gateway.handle_tool_call(req)
        
        with open("test_audit.jsonl", "r") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            log = json.loads(lines[0])
            self.assertEqual(log["tool"], "delete_db")
            self.assertEqual(log["decision"], "DENIED")

if __name__ == '__main__':
    unittest.main()
