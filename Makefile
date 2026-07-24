.PHONY: install dev test lint fmt chat evals build deploy zip

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt

test:
	ANTHROPIC_MOCK=1 STORE_BACKEND=memory pytest -q

lint:
	ruff check .

fmt:
	ruff check --fix .
	ruff format .

chat:
	ANTHROPIC_MOCK=1 STORE_BACKEND=memory python scripts/local_chat.py

evals:
	ANTHROPIC_MOCK=1 python evals/run_evals.py

build:
	sam build

deploy: build
	sam deploy --guided

zip:
	git archive --format=zip -o multi-agent-customer-service.zip HEAD
