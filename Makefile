CLI_VERSION := $(shell uv version --short)

.PHONY: help
help: ## Show this help message
	@echo "Knowledge Stack CLI: $(CLI_VERSION)"
	@echo "Available commands:"
	@grep -hE '^[a-zA-Z0-9_-]+:.*## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' | sort


.PHONY: install-dev
install-dev: ## Install dependencies and pre-commit hooks
	@uv sync --all-extras --group dev
	@uv run pre-commit install

.PHONY: fix
fix: ## Run the linter and fix the issues
	@uv run ruff check --fix

.PHONY: lint
lint: ## Run the linter
	@uv run ruff check

.PHONY: typecheck
typecheck: ## Run the type checker
	@uv run basedpyright --stats

.PHONY: test
test: ## Run unit tests
	@uv run pytest tests/ -v --ignore=tests/e2e

.PHONY: wait-for-api
wait-for-api: ## Wait for the e2e API to be ready
	@echo "Waiting for API at http://localhost:28000..."
	@for i in $$(seq 1 120); do \
		if curl -sf http://localhost:28000/healthz > /dev/null 2>&1; then \
			echo "API is ready"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "Timed out waiting for API after 120s"; \
	exit 1

.PHONY: e2e-test
e2e-test: wait-for-api ## Run e2e tests (requires running backend)
	@uv run pytest tests/e2e/ -v -m e2e -n 2

.PHONY: local-login
local-login: ## Login to local dev API (assumes dev-stack + dev-api running)
	@API_URL=https://localhost:18000; \
	USER_ID=00000000-0000-0000-0001-000000000001; \
	TENANT_ID=00000000-0000-0000-0002-000000000001; \
	TOKEN=$$(curl -sk -X POST $$API_URL/system/auth/assume_user \
		-H "Authorization: Bearer dev-admin-api-key" \
		-H "Content-Type: application/json" \
		-d "{\"user_id\": \"$$USER_ID\", \"tenant_id\": \"$$TENANT_ID\"}" \
		| python3 -c "import sys,json; print(json.load(sys.stdin)['token'])") && \
	API_KEY=$$(curl -sk -X POST $$API_URL/v1/api-keys \
		-H "Cookie: ks_uat=$$TOKEN" \
		-H "Content-Type: application/json" \
		-d '{"name": "cli-dev"}' \
		| python3 -c "import sys,json; print(json.load(sys.stdin)['key'])") && \
	uv run kscli settings environment local --url $$API_URL && \
	uv run kscli login --api-key $$API_KEY && \
	uv run kscli whoami

.PHONY: pre-commit
pre-commit: lint typecheck test ## Run linting, typechecking, and tests