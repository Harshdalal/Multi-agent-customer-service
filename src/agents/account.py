from shared.config import get_settings

from .base import Agent
from .prompts import ACCOUNT

# Account work is high-volume and low-ambiguity, so it runs on the cheaper model.
AGENT = Agent(name="account", model=get_settings().router_model, system=ACCOUNT)
