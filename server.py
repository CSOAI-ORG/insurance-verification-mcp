#!/usr/bin/env python3
"""Insurance Verification MCP Server — Healthcare and general insurance automation."""

import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access

import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("insurance-verification-mcp")


@mcp.tool(name="verify_eligibility")
async def verify_eligibility(
    patient_id: str, policy_number: str, procedure_code: str, api_key: str = ""
) -> str:
    # Simulated verification
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    return {
        "patient_id": patient_id,
        "policy_number": policy_number,
        "procedure_code": procedure_code,
        "eligible": True,
        "copay": 25.0,
    }


@mcp.tool(name="prior_authorization_check")
async def prior_authorization_check(
    diagnosis_code: str, treatment: str, api_key: str = ""
) -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    requires_auth = treatment.lower() in ["surgery", "mri", "specialist_visit"]
    return {
        "diagnosis_code": diagnosis_code,
        "treatment": treatment,
        "requires_prior_auth": requires_auth,
        "estimated_days": 3 if requires_auth else 0,
    }


@mcp.tool(name="claim_status")
async def claim_status(claim_id: str, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    return {
        "claim_id": claim_id,
        "status": "approved",
        "amount": 1240.0,
        "paid_date": "2026-04-10",
    }


@mcp.tool(name="fraud_indicators")
async def fraud_indicators(claim_data: dict, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    flags = []
    if claim_data.get("amount", 0) > 50000:
        flags.append("High value claim")
    if claim_data.get("provider_history_months", 99) < 3:
        flags.append("New provider")
    return {"flags": flags, "risk_score": min(100, len(flags) * 30 + 10)}


if __name__ == "__main__":
    mcp.run()
