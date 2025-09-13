.PHONY: dev test typecheck fmt gen install clean \
        ecr-login docker-build-api docker-push-api apprunner-update

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

# --- Deployment helpers (API → ECR → App Runner) ---
# Required env vars:
#   AWS_ACCOUNT_ID, AWS_REGION
# Optional:
#   ECR_REPO (default: llm-txt-api), APP_RUNNER_SERVICE_ARN

ECR_REPO ?= llm-txt-api
AWS_REGION ?= us-east-1
REGISTRY = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
IMAGE_URI = $(REGISTRY)/$(ECR_REPO)

ecr-login:
	@if [ -z "$(AWS_ACCOUNT_ID)" ]; then echo "Set AWS_ACCOUNT_ID env var"; exit 1; fi
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(REGISTRY)

docker-build-api:
	@if [ -z "$(AWS_ACCOUNT_ID)" ]; then echo "Set AWS_ACCOUNT_ID env var"; exit 1; fi
	docker build -f Dockerfile.api -t $(IMAGE_URI):latest -t $(IMAGE_URI):$$(git rev-parse --short HEAD) .

docker-push-api:
	@if [ -z "$(AWS_ACCOUNT_ID)" ]; then echo "Set AWS_ACCOUNT_ID env var"; exit 1; fi
	docker push $(IMAGE_URI):latest
	docker push $(IMAGE_URI):$$(git rev-parse --short HEAD)

apprunner-update:
	@if [ -z "$(APP_RUNNER_SERVICE_ARN)" ]; then echo "Set APP_RUNNER_SERVICE_ARN env var"; exit 1; fi
	aws apprunner update-service \
	  --service-arn "$(APP_RUNNER_SERVICE_ARN)" \
	  --source-configuration "ImageRepository={ImageIdentifier=$(IMAGE_URI):latest,ImageRepositoryType=ECR},AutoDeploymentsEnabled=true"
