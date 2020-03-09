.PHONY: test kafka migrate web aweb

DEBUG?=--debug
LOG_LEVEL?=INFO
RUN=pipenv run

test:
	$(RUN) pytest -v --cov action_man --cov-report term --cov-config .coveragerc --disable-warnings t

mypy:
	$(RUN) mypy action_man/

migrate:
	$(RUN) alembic upgrade head

kafka: migrate
	$(RUN) faust -A action_man.entrypoint.kafka -l $(LOG_LEVEL) $(DEBUG) worker

webdev: migrate
	$(RUN) python action_man/entrypoint.py

web: migrate
	$(RUN) uvicorn action_man.entrypoint:web --host 0.0.0.0 --port 8000
