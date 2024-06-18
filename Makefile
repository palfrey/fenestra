requirements.txt: requirements.in uv
	./uv pip compile requirements.in -o requirements.txt