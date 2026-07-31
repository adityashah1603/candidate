.PHONY: demo test

demo:
	PYTHONPATH=. python3 demo.py

test:
	PYTHONPATH=. python3 -m unittest discover -s tests -v
