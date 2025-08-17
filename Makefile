.PHONY: dev test typecheck fmt gen install clean

install:
	pip install -e ".[dev]"
	playwright install

dev:
	uvicorn llm_txt.api:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v

typecheck:
	mypy llm_txt/

fmt:
	black llm_txt/ tests/
	ruff check --fix llm_txt/ tests/

gen:
	python -m llm_txt.cli generate --url $(URL) --depth $(DEPTH) --full $(FULL)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/