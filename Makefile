.PHONY: install run clean

install:
	poetry install

run:
	poetry run python src/main.py

serve:
	poetry run uvicorn src.api.app:app --reload

clean:
	rm -rf `find . -type d -name "__pycache__"`
	rm -rf .pytest_cache
	rm -rf .venv
	rm -rf poetry.lock
