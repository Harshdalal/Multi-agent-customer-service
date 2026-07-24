from shared.config import get_settings

from .base import Agent
from .prompts import TECHNICAL

AGENT = Agent(name="technical", model=get_settings().specialist_model, system=TECHNICAL)
