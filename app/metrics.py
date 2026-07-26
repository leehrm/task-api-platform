from prometheus_client import Counter, Histogram


HTTP_REQUEST_TOTAL = Counter(
    "http_request_total",
    "Total number of HTTP requests",
    ["method", "path", "status"],
)

CACHE_HIT_TOTAL = Counter(
    "cache_hit_total",
    "Total number of cache hits",
)

CACHE_MISS_TOTAL = Counter(
    "cache_miss_total",
    "Total number of cache misses",
)

NOTIFICATION_SENT_TOTAL = Counter(
    "notification_sent_total",
    "Total number of notifications sent",
    ["channel"],
)

NOTIFICATION_FAILED_TOTAL = Counter(
    "notification_failed_total",
    "Total number of notifications that failed to send",
    ["channel"],
)

DB_QUERY_LATENCY_SECONDS = Histogram(
    "db_query_latency_seconds",
    "Database query latency in seconds",
    ["operation", "target"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5, 5.0),
)
