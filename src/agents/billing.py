from shared.config import get_settings

from .base import Agent
from .prompts import BILLING

AGENT = Agent(name="billing", model=get_settings().specialist_model, system=BILLING)
