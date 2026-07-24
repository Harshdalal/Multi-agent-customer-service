"""Name -> Agent map the coordinator dispatches on."""
from .account import AGENT as account
from .billing import AGENT as billing
from .escalation import AGENT as escalation
from .technical import AGENT as technical

AGENT_MAP = {
    "billing": billing,
    "technical": technical,
    "account": account,
    "escalation": escalation,
}
