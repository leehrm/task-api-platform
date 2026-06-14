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

DB_QUERY_LATENCY_SECONDS = Histogram(
    "db_query_latency_seconds",
    "Database query latency in seconds",
    ["operation", "target"],
)
