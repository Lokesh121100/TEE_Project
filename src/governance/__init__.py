# 🛡️ ARIA Governance Module
# Multi-layer AI governance, audit logging, and compliance framework

from .audit_logging import (
    AuditLoggingService,
    AuditLogEntry,
    GuardrailChecks,
    AuditDecisionType
)

from .bias_detection import (
    BiasDetectionService,
    FairnessMetric
)

from .escalation_rules import (
    EscalationRulesEngine,
    EscalationDecision,
    EscalationLevel,
    EscalationTeam
)

from .cost_governance import (
    CostGovernanceService,
    CostBreakdown
)

from .governance_api import router

__all__ = [
    'AuditLoggingService',
    'AuditLogEntry',
    'GuardrailChecks',
    'AuditDecisionType',
    'BiasDetectionService',
    'FairnessMetric',
    'EscalationRulesEngine',
    'EscalationDecision',
    'EscalationLevel',
    'EscalationTeam',
    'CostGovernanceService',
    'CostBreakdown',
    'router'
]

print("[OK] Intelsoft ARIA Governance Framework Initialized")
print("   - Audit Logging: [OK] Active")
print("   - Bias Detection: [OK] Active")
print("   - Escalation Rules: [OK] Active")
print("   - Cost Governance: [OK] Active")

