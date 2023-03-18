init:
	pip install -r requirements.txt

test:
	python __init__.py "google" -s "01 March 2023" -e "02 March 2023" -l "id"

.PHONY: init test
