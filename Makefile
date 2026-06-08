.venv/bin/activate:
	uv venv --system-site-packages --python-preference=only-system

.PHONY: sync
sync: .venv/bin/activate
	uv sync

run: sync
	uv run python fenestra.py

dormer-load: sync
	uv run dormer load

pre-commit: sync
	uv run pre-commit run -a
