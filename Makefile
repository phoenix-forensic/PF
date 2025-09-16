.PHONY: api android firewall lint

api:
	cd api && python artefato_tracker.py

android:
	cd modules/PFandroid && ./gradlew assembleDebug

firewall:
	cd firewall && python symbio_dns.py --show

lint:
	python -m compileall api firewall
