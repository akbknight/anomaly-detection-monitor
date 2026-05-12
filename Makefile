.PHONY: run test clean

run:
	python detect.py

test:
	python -m pytest tests/ -v

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
