# Gunicorn config variables
loglevel = "info"
errorlog = "-"  # stderr
accesslog = "-"  # stdout
worker_tmp_dir = "/dev/shm"
graceful_timeout = 120
timeout = 120
keepalive = 5
threads = 3
workers = 6
worker_class = 'gevent'
worker_connections = 1024

# --workers=4 --threads=2 --worker-class=gthread --worker-tmp-dir /dev/shm --timeout 120 --keep-alive 90
