all: clean test run

test:
	python check_token.py

run:
	@echo "Running the program..."
	@python ./test.py

clean:
	@echo "Cleaning log directory..."
	@find ./logs -type f | sort | head -n -1 | xargs rm -f

cleanrawdata:
	@echo "Cleaning data directory..."
	@find ./data/raw -type f | xargs rm -rf
