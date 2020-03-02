.PHONY: test kafka migrate

DEBUG?=--debug
LOG_LEVEL?=DEBUG
RUN=pipenv run

test:
	$(RUN) pytest -v --cov action_man --cov-report term --cov-config .coveragerc test

mypy:
	$(RUN) mypy action_man/

migrate:
	$(RUN) alembic upgrade head

kafka: migrate
	$(RUN) faust -A action_man.entrypoint.kafka -l $(LOG_LEVEL) $(DEBUG) worker

demo: migrate
	$(RUN) faust -A action_man.demo:kapp -l INFO $(DEBUG) worker

webdev: migrate
	$(RUN) python action_man/entrypoint.py

web: migrate
	$(RUN) gunicorn action_man.entrypoint:web --bind 0.0.0.0:8000 --worker-class sanic.worker.GunicornWorker
