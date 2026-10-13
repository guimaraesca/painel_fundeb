.PHONY: payload panel all
payload:
	python src/build_payload.py
panel: payload
	python src/build_panel.py
all: panel
