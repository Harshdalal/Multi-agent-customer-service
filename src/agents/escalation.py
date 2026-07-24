from shared.config import get_settings

from .base import Agent
from .prompts import ESCALATION

AGENT = Agent(name="escalation", model=get_settings().specialist_model, system=ESCALATION)
