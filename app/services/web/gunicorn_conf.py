# Gunicorn config variables
loglevel = 'info'
errorlog = '-'  # stderr
accesslog = '-'  # stdout
# Docker container: single process, no multi-tenancy
# Using /dev/shm for performance in containerized environment
worker_tmp_dir = '/dev/shm'  # noqa: S108
graceful_timeout = 120
timeout = 120
keepalive = 5
threads = 3
workers = 6
worker_class = 'gevent'
worker_connections = 1024
