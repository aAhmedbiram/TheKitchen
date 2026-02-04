# Gunicorn configuration file

# Server socket
bind = "0.0.0.0:8080"

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000

# Timeout settings
timeout = 120
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "the-kitchen"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None

# Graceful shutdown
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
