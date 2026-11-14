# The public explorer of the review, the "SOSA/SSN Usage Observatory" (README.md), and its
# deployment on ci.mines-stetienne.fr: a container (deploy/compose.yaml, 127.0.0.1:8115) behind
# Apache, under /sosa-ssn-observatory/ (deploy/sosa-ssn-observatory.conf, in sites-available).
# `make deploy` opens one SSH connection, after three beeps: touch the YubiKey.

CI    ?= ci
DIR   ?= /var/www/sosa-ssn-observatory
STAGE ?= /tmp/sosa-ssn-observatory-deploy
BEEP   = for i in 1 2 3; do paplay /usr/share/sounds/freedesktop/stereo/bell.oga 2>/dev/null || printf '\a'; done
FILES  = index.html app.js style.css examples.js kg-worker.js README.md
EXTRA  = $(wildcard sw.js sparklis vendor)

.PHONY: public deploy clean

# the public version: no quotation of the works (Maxime, 2026-11-14)
public:
	rm -rf build/public build/deploy
	mkdir -p build/public/data build/deploy
	cd .. && python3 -I scripts/build_kg.py --public explorer/build/public/data
	cp $(FILES) build/public/
	$(if $(EXTRA),cp -r $(EXTRA) build/public/,)
	cp deploy/Dockerfile deploy/compose.yaml deploy/serve.py deploy/sosa-ssn-observatory.conf build/deploy/

# one connection: the site and the container, the Apache site, a configuration test, a reload
deploy: public
	$(BEEP); tar -C build -czf - public deploy | ssh $(CI) \
	  'set -e; sudo install -d -o $$(id -un) -g $$(id -gn) $(DIR) $(DIR)/site $(DIR)/deploy; \
	   mkdir -p $(STAGE); tar -C $(STAGE) -xzf -; \
	   rsync -a --delete $(STAGE)/public/ $(DIR)/site/; rsync -a --delete $(STAGE)/deploy/ $(DIR)/deploy/; \
	   cd $(DIR)/deploy && sudo docker compose up -d --build 2>&1 | tail -2; sleep 3; curl -sf http://127.0.0.1:8115/healthz | grep -qx ok || { echo "the observatory container does not answer on 8115: Apache left as it was"; exit 1; }; \
	   sudo cp $(DIR)/deploy/sosa-ssn-observatory.conf /etc/apache2/sites-available/sosa-ssn-observatory.conf; \
	   sudo a2ensite -q sosa-ssn-observatory; sudo rm -f /etc/apache2/conf-enabled/sosa-ssn-observatory.conf; \
	   sudo apache2ctl configtest && sudo systemctl reload apache2; \
	   curl -s -o /dev/null -w "%{http_code}\n" https://ci.mines-stetienne.fr/sosa-ssn-observatory/'

clean:
	rm -rf build
