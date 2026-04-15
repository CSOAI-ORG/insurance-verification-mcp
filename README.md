# Insurance Verification

> By [MEOK AI Labs](https://meok.ai) — Healthcare and general insurance automation

## Installation

```bash
pip install insurance-verification-mcp
```

## Usage

```bash
python server.py
```

## Tools

### `verify_eligibility`
Verify patient insurance eligibility including coverage dates and plan details.

**Parameters:**
- `patient_id` (str): Patient identifier
- `policy_number` (str): Insurance policy number
- `procedure_code` (str): Procedure code to check

### `prior_authorization_check`
Check if a medical procedure requires prior authorization from the insurer.

**Parameters:**
- `diagnosis_code` (str): Diagnosis code
- `treatment` (str): Treatment type (e.g. surgery, mri, specialist_visit)

### `claim_status`
Check the status of an insurance claim including processing stage and expected dates.

**Parameters:**
- `claim_id` (str): Claim identifier

### `fraud_indicators`
Analyze a claim for potential fraud indicators and risk scoring.

**Parameters:**
- `claim_data` (dict): Claim data including amount, provider_history_months, etc.

## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT — MEOK AI Labs
