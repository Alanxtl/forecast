all: clean test run

test:
	@echo $$(python src/crawler/graphql/graphql.py) > output.json; \
	python check_token.py output.json
	@rm output.json > /dev/null

run:
	@echo "Running the program..."
	@python ./test.py

clean:
	@echo "Cleaning log directory..."
	@find ./logs -type f | sort | head -n -1 | xargs rm -f
