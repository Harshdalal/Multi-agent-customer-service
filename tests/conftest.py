import os
import pathlib
import sys

os.environ.setdefault("ANTHROPIC_MOCK", "1")
os.environ.setdefault("STORE_BACKEND", "memory")

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
