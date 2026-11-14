# The SOSA/SSN Usage Observatory in one small image: a standard-library static server. The
# site itself (the public build) is not in the image: it is mounted read only from
# /var/www/sosa-ssn-observatory/site, so that a new release of the data needs no rebuild.
# The digest is that of python:3.12-slim on 2026-11-11 (the review application uses the same).
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TZ=Europe/Paris
WORKDIR /app
COPY serve.py /app/serve.py
RUN useradd --uid 10002 --no-create-home --shell /usr/sbin/nologin observatory
USER 10002
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"
CMD ["python3", "-I", "/app/serve.py", "--root", "/site", "--host", "0.0.0.0", "--port", "8000"]
