PYTHON ?= python3
VENV_DIR ?= .venv
PIP := $(VENV_DIR)/bin/pip
PYTHON_BIN := $(VENV_DIR)/bin/python
SCRIPT := crop_screenshots.py
INPUT_DIR ?= assets
TOP ?= 32
BOTTOM ?= 18
LEFT ?= 0
RIGHT ?= 0

.PHONY: help setup install crop dry-run clean

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make setup    - Create the virtual environment and install dependencies' \
		'  make crop     - Crop screenshots in $(INPUT_DIR) in place' \
		'  make dry-run  - Show the crop plan without modifying files' \
		'  make clean    - Remove the virtual environment'

setup: $(VENV_DIR)/bin/python

$(VENV_DIR)/bin/python:
	$(PYTHON) -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install: setup

crop: setup
	$(PYTHON_BIN) $(SCRIPT) --input-dir $(INPUT_DIR) --top $(TOP) --bottom $(BOTTOM) --left $(LEFT) --right $(RIGHT)

dry-run: setup
	$(PYTHON_BIN) $(SCRIPT) --input-dir $(INPUT_DIR) --top $(TOP) --bottom $(BOTTOM) --left $(LEFT) --right $(RIGHT) --dry-run

clean:
	rm -rf $(VENV_DIR)