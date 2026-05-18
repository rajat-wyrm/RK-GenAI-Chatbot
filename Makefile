.PHONY: install backend frontend docker run lint test clean

install:
	cd rk-core && pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd rk-core && uvicorn main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

docker:
	docker compose up --build

lint:
	cd rk-core && ruff check .
	cd frontend && npm run lint

test:
	cd rk-core && pytest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
