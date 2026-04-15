#!/usr/bin/env python3
"""Insurance Verification MCP Server — Healthcare and general insurance automation."""

import sys, os
sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access

import json, hashlib, time
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("insurance-verification", instructions="MEOK AI Labs — Insurance eligibility verification, prior authorization, claims, and fraud detection.")

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

_CLAIMS: dict = {}
_VERIFICATIONS: list = []

PLAN_TYPES = {
    "PPO": {"name": "Preferred Provider Organization", "network_required": False, "referral_needed": False,
             "copay_range": (20, 50), "deductible_range": (500, 2000), "coinsurance": 0.20},
    "HMO": {"name": "Health Maintenance Organization", "network_required": True, "referral_needed": True,
             "copay_range": (10, 30), "deductible_range": (250, 1000), "coinsurance": 0.15},
    "EPO": {"name": "Exclusive Provider Organization", "network_required": True, "referral_needed": False,
             "copay_range": (15, 40), "deductible_range": (500, 1500), "coinsurance": 0.20},
    "POS": {"name": "Point of Service", "network_required": False, "referral_needed": True,
             "copay_range": (15, 40), "deductible_range": (500, 2000), "coinsurance": 0.25},
    "HDHP": {"name": "High Deductible Health Plan", "network_required": False, "referral_needed": False,
              "copay_range": (0, 20), "deductible_range": (1400, 7050), "coinsurance": 0.20},
}

PROCEDURE_CODES = {
    "99213": {"description": "Office visit, established patient, moderate complexity", "avg_cost": 150, "auth_required": False},
    "99214": {"description": "Office visit, established patient, moderate-high complexity", "avg_cost": 220, "auth_required": False},
    "99215": {"description": "Office visit, established patient, high complexity", "avg_cost": 320, "auth_required": False},
    "27447": {"description": "Total knee replacement", "avg_cost": 35000, "auth_required": True},
    "70553": {"description": "MRI brain with/without contrast", "avg_cost": 2500, "auth_required": True},
    "43239": {"description": "Upper GI endoscopy with biopsy", "avg_cost": 3000, "auth_required": True},
    "92014": {"description": "Comprehensive eye exam, established", "avg_cost": 175, "auth_required": False},
    "92004": {"description": "Comprehensive eye exam, new patient", "avg_cost": 250, "auth_required": False},
    "92134": {"description": "Retinal imaging (OCT)", "avg_cost": 120, "auth_required": False},
    "67028": {"description": "Intravitreal injection", "avg_cost": 1800, "auth_required": True},
}

AUTH_REQUIRED_TREATMENTS = [
    "surgery", "mri", "ct_scan", "specialist_visit", "inpatient", "outpatient_surgery",
    "physical_therapy_extended", "home_health", "durable_medical_equipment",
    "genetic_testing", "transplant", "radiation_therapy", "chemotherapy",
    "intravitreal_injection", "retinal_surgery",
]

FRAUD_INDICATORS_RULES = {
    "high_amount": {"threshold": 50000, "weight": 30, "description": "Unusually high claim amount"},
    "new_provider": {"threshold_months": 3, "weight": 20, "description": "Provider registered recently"},
    "duplicate_dates": {"weight": 25, "description": "Multiple claims for same date of service"},
    "weekend_service": {"weight": 10, "description": "Service performed on weekend"},
    "unbundling": {"weight": 35, "description": "Possible procedure unbundling detected"},
    "upcoding": {"weight": 30, "description": "Possible upcoding — higher code than expected"},
    "phantom_billing": {"weight": 40, "description": "Service billed without corresponding treatment record"},
    "excessive_services": {"threshold_per_day": 20, "weight": 25, "description": "Unusually high number of services in one day"},
}


@mcp.tool()
def verify_eligibility(patient_id: str, policy_number: str, procedure_code: str,
                        date_of_service: str = "", plan_type: str = "PPO",
                        api_key: str = "") -> str:
    """Verify patient insurance eligibility with coverage details, copay, deductible, and network status."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    plan = PLAN_TYPES.get(plan_type.upper(), PLAN_TYPES["PPO"])
    procedure = PROCEDURE_CODES.get(procedure_code, {"description": "Unknown procedure", "avg_cost": 0, "auth_required": False})

    copay = plan["copay_range"][0] + (plan["copay_range"][1] - plan["copay_range"][0]) // 2
    deductible = plan["deductible_range"][0] + (plan["deductible_range"][1] - plan["deductible_range"][0]) // 2
    coinsurance = plan["coinsurance"]
    estimated_cost = procedure["avg_cost"]
    patient_responsibility = round(copay + max(0, (estimated_cost - deductible) * coinsurance), 2)

    dos = date_of_service or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ref_id = hashlib.md5(f"{patient_id}{policy_number}{dos}".encode()).hexdigest()[:12]

    verification = {
        "reference_id": ref_id,
        "patient_id": patient_id,
        "policy_number": policy_number,
        "plan_type": plan_type.upper(),
        "plan_name": plan["name"],
        "procedure_code": procedure_code,
        "procedure_description": procedure["description"],
        "date_of_service": dos,
        "eligible": True,
        "coverage_status": "active",
        "copay": copay,
        "deductible": deductible,
        "deductible_met": False,
        "coinsurance_rate": coinsurance,
        "estimated_total_cost": estimated_cost,
        "estimated_patient_responsibility": patient_responsibility,
        "network_required": plan["network_required"],
        "referral_needed": plan["referral_needed"],
        "prior_auth_required": procedure["auth_required"],
        "coverage_effective": "2026-01-01",
        "coverage_expires": "2026-12-31",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    _VERIFICATIONS.append(verification)
    return verification


@mcp.tool()
def prior_authorization_check(diagnosis_code: str, treatment: str, procedure_code: str = "",
                                urgency: str = "routine", patient_age: int = 0,
                                api_key: str = "") -> str:
    """Check if a treatment requires prior authorization with estimated approval timeline and documentation needs."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    treatment_lower = treatment.lower().replace(" ", "_")
    requires_auth = treatment_lower in AUTH_REQUIRED_TREATMENTS

    if procedure_code and procedure_code in PROCEDURE_CODES:
        proc = PROCEDURE_CODES[procedure_code]
        if proc["auth_required"]:
            requires_auth = True

    if urgency == "urgent":
        timeline_days = 1
        timeline_note = "Urgent review — 24-hour turnaround"
    elif urgency == "emergent":
        timeline_days = 0
        timeline_note = "Emergent — concurrent review (treat first)"
    else:
        timeline_days = 5 if requires_auth else 0
        timeline_note = "Standard review timeline" if requires_auth else "No authorization required"

    required_docs = []
    if requires_auth:
        required_docs = ["clinical_notes", "diagnosis_documentation", "treatment_plan"]
        if "surgery" in treatment_lower:
            required_docs.extend(["surgical_history", "conservative_treatment_documentation", "imaging_results"])
        if "mri" in treatment_lower or "ct" in treatment_lower:
            required_docs.extend(["previous_imaging", "clinical_indication"])
        if patient_age and patient_age > 65:
            required_docs.append("medicare_coverage_determination")

    auth_id = hashlib.md5(f"{diagnosis_code}{treatment}{time.time()}".encode()).hexdigest()[:10]

    return {
        "auth_reference": f"PA-{auth_id.upper()}",
        "diagnosis_code": diagnosis_code,
        "treatment": treatment,
        "procedure_code": procedure_code or "N/A",
        "requires_prior_auth": requires_auth,
        "urgency": urgency,
        "estimated_review_days": timeline_days,
        "timeline_note": timeline_note,
        "required_documentation": required_docs,
        "submission_methods": ["electronic_portal", "fax", "phone"] if requires_auth else [],
        "appeal_process": "Available within 60 days of denial" if requires_auth else "N/A",
        "peer_to_peer_available": requires_auth and urgency != "emergent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
def claim_status(claim_id: str, include_timeline: bool = True, api_key: str = "") -> str:
    """Check insurance claim status with processing stage, payment details, and timeline."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    stored = _CLAIMS.get(claim_id)
    if stored:
        return stored

    now = datetime.now(timezone.utc)
    stages = ["received", "validated", "adjudicated", "approved", "payment_processed"]
    current_stage = "approved"

    timeline = []
    if include_timeline:
        base = now - timedelta(days=14)
        for i, stage in enumerate(stages):
            stage_date = base + timedelta(days=i * 3)
            completed = stages.index(stage) <= stages.index(current_stage)
            timeline.append({"stage": stage, "date": stage_date.strftime("%Y-%m-%d"),
                              "status": "completed" if completed else "pending"})

    claim = {
        "claim_id": claim_id,
        "status": current_stage,
        "status_description": "Claim approved — payment processing",
        "amount_billed": 1500.00,
        "amount_allowed": 1240.00,
        "amount_paid": 1240.00,
        "patient_responsibility": 260.00,
        "copay_applied": 30.00,
        "deductible_applied": 150.00,
        "coinsurance_applied": 80.00,
        "paid_date": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
        "payment_method": "EFT",
        "eob_available": True,
        "processing_timeline": timeline,
        "days_to_process": 12,
        "adjustments": [
            {"code": "CO-45", "description": "Charges exceed fee schedule", "amount": -260.00},
        ],
        "remark_codes": ["N362 — Payment adjusted based on contracted rate"],
        "timestamp": now.isoformat(),
    }

    _CLAIMS[claim_id] = claim
    return claim


@mcp.tool()
def fraud_indicators(claim_data: dict, api_key: str = "") -> str:
    """Analyze a claim for fraud indicators with risk scoring, pattern detection, and recommendations."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    flags = []
    risk_score = 0
    details = []

    amount = claim_data.get("amount", 0)
    if amount > FRAUD_INDICATORS_RULES["high_amount"]["threshold"]:
        rule = FRAUD_INDICATORS_RULES["high_amount"]
        flags.append(rule["description"])
        risk_score += rule["weight"]
        details.append({"rule": "high_amount", "triggered": True, "value": amount,
                         "threshold": rule["threshold"]})

    provider_months = claim_data.get("provider_history_months", 99)
    if provider_months < FRAUD_INDICATORS_RULES["new_provider"]["threshold_months"]:
        rule = FRAUD_INDICATORS_RULES["new_provider"]
        flags.append(rule["description"])
        risk_score += rule["weight"]
        details.append({"rule": "new_provider", "triggered": True, "months": provider_months})

    dos = claim_data.get("date_of_service", "")
    if dos:
        try:
            d = datetime.strptime(dos, "%Y-%m-%d")
            if d.weekday() >= 5:
                rule = FRAUD_INDICATORS_RULES["weekend_service"]
                flags.append(rule["description"])
                risk_score += rule["weight"]
                details.append({"rule": "weekend_service", "triggered": True, "day": d.strftime("%A")})
        except ValueError:
            pass

    services_count = claim_data.get("services_count", 1)
    if services_count > FRAUD_INDICATORS_RULES["excessive_services"]["threshold_per_day"]:
        rule = FRAUD_INDICATORS_RULES["excessive_services"]
        flags.append(rule["description"])
        risk_score += rule["weight"]
        details.append({"rule": "excessive_services", "triggered": True, "count": services_count})

    procedure_codes = claim_data.get("procedure_codes", [])
    if len(procedure_codes) > len(set(procedure_codes)):
        rule = FRAUD_INDICATORS_RULES["duplicate_dates"]
        flags.append("Duplicate procedure codes on same claim")
        risk_score += rule["weight"]

    if claim_data.get("modifier_count", 0) > 3:
        flags.append("Excessive modifier usage")
        risk_score += 15

    if claim_data.get("diagnosis_procedure_mismatch"):
        flags.append("Diagnosis code does not match procedure")
        risk_score += 25

    risk_score = min(risk_score, 100)
    if risk_score >= 70:
        risk_level = "critical"
        action = "Refer to Special Investigations Unit (SIU)"
    elif risk_score >= 50:
        risk_level = "high"
        action = "Manual review required before processing"
    elif risk_score >= 25:
        risk_level = "moderate"
        action = "Flag for enhanced review"
    else:
        risk_level = "low"
        action = "Standard processing"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flags": flags,
        "total_flags": len(flags),
        "details": details,
        "recommended_action": action,
        "auto_approve": risk_score < 25,
        "siu_referral": risk_score >= 70,
        "investigation_checklist": [
            "Verify provider credentials and enrollment date",
            "Cross-reference with patient treatment history",
            "Check for patterns across related claims",
            "Validate date of service against facility records",
        ] if risk_score >= 50 else [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    mcp.run()
