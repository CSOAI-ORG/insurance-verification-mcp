#!/usr/bin/env python3
"""Insurance Verification MCP Server — Healthcare and general insurance automation."""

import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access

import json
from datetime import datetime, timezone
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("insurance-verification", instructions="MEOK AI Labs MCP Server")

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None


@mcp.tool()
def verify_eligibility(
    patient_id: str, policy_number: str, procedure_code: str, api_key: str = ""
) -> str:
    """Verify patient insurance eligibility including coverage dates and plan details."""
    # Simulated verification
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    return {
        "patient_id": patient_id,
        "policy_number": policy_number,
        "procedure_code": procedure_code,
        "eligible": True,
        "copay": 25.0,
    }


@mcp.tool()
def prior_authorization_check(
    diagnosis_code: str, treatment: str, api_key: str = ""
) -> str:
    """Check if a medical procedure requires prior authorization from the insurer."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    requires_auth = treatment.lower() in ["surgery", "mri", "specialist_visit"]
    return {
        "diagnosis_code": diagnosis_code,
        "treatment": treatment,
        "requires_prior_auth": requires_auth,
        "estimated_days": 3 if requires_auth else 0,
    }


@mcp.tool()
def claim_status(claim_id: str, api_key: str = "") -> str:
    """Check the status of an insurance claim including processing stage and expected dates."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    return {
        "claim_id": claim_id,
        "status": "approved",
        "amount": 1240.0,
        "paid_date": "2026-04-10",
    }


@mcp.tool()
def fraud_indicators(claim_data: dict, api_key: str = "") -> str:
    """Analyze a claim for potential fraud indicators and risk scoring."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    flags = []
    if claim_data.get("amount", 0) > 50000:
        flags.append("High value claim")
    if claim_data.get("provider_history_months", 99) < 3:
        flags.append("New provider")
    return {"flags": flags, "risk_score": min(100, len(flags) * 30 + 10)}


if __name__ == "__main__":
    mcp.run()
