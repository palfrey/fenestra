requirements.txt: requirements.in uv
	./uv pip compile requirements.in -o requirements.txt

.venv/bin/activate:
	./uv venv --system-site-packages --python-preference=only-system

.PHONY: sync
sync: .venv/bin/activate requirements.txt
	./uv pip sync requirements.txt

run: sync
	./uv run python fenestra.py

dormer-load: sync
	./uv run dormer load

pre-commit: sync
	./uv run pre-commit run -a
