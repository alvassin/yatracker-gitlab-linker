PROJECT_NAME ?= yatracker_gitlab_linker
VERSION = $(shell poetry version --short | tr '+' '-')
POETRY_LOCATION=$(shell poetry env info -p)

all:
	@echo "make devenv     - Configure the development environment"
	@echo "make clean      - Remove files which creates by distutils"
	@echo "make lint       - Syntax & code style check"
	@echo "make codestyle  - Reformat code with gray linter"
	@echo "make test       - Test this project"
	@exit 0

clean:
	rm -fr *.egg-info .tox dist .cache
	find . -iname '*.pyc' -delete

devenv: clean
	rm -rf $(POETRY_LOCATION)
	poetry install

codestyle:
	poetry run gray *.py $(PROJECT_NAME) tests

lint:
	poetry check -q
	poetry run pylama .
	poetry run unify --quote "'" --check-only --recursive $(PROJECT_NAME) tests
	poetry run mypy --install-types --non-interactive $(PROJECT_NAME) tests

test: clean lint
	poetry run pytest --cov $(PROJECT_NAME) --cov-report term-missing

sdist:
	poetry build -f sdist
