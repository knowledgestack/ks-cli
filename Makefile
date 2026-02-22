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

.PHONY: pre-commit
pre-commit: lint typecheck test ## Run linting, typechecking, and tests