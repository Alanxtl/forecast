GIT := $(shell command -v git)

check: check-git check-token
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
run:
	@echo "Running the program..."
	@python ./test.py

clean:
	@echo "Cleaning log directory..."
	@find ./logs -type f | sort | head -n -1 | xargs rm -f

cleanrawdata:
	@echo "Cleaning data directory..."
	@find ./data/raw -type f | xargs rm -rf
