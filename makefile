GIT := $(shell command -v git)
CLOC := $(shell command -v cloc)

check: check-git check-cloc check-token
all: clean check run

check-token:
	@python check_token.py

check-git:
	@if [ -x "$(GIT)" ]; then \
		echo "git installed, located in: $(GIT)"; \
	else \
		echo "git command not found, please install git first"; \
		exit 1; \
	fi

check-cloc:
	@if [ -x "$(CLOC)" ]; then \
		echo "cloc installed, located in: $(CLOC)"; \
	else \
		echo "cloc command not found, please install cloc first: https://github.com/AlDanial/cloc?tab=readme-ov-file#install-via-package-manager"; \
		exit 1; \
	fi

run:
	@echo "Running the program..."
	@python ./test.py

clean:
	@echo "Cleaning log directory..."
	@find ./logs -type f | sort | head -n -1 | xargs rm -f

cleanrawdata:
	@echo "Cleaning data directory..."
	@find ./data/raw -type f | xargs rm -rf

builddata:
	python ./src/builder/dataset_builder.py
