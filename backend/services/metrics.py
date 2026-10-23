"""
Prometheus Metrics Instrumentation for SevaDristi
Tracks API latencies, computer vision heuristic scores, reconciler scores, and verification outcomes.
"""

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# 1. API Request Latency
REQUEST_LATENCY = Histogram(
    "sevadristi_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# 2. Vision Gate Blur Score Histogram
VISION_BLUR_SCORE = Histogram(
    "sevadristi_vision_blur_score",
    "Variance of Laplacian sharpness score distribution",
    buckets=[20.0, 50.0, 80.0, 110.0, 150.0, 200.0, 300.0, 500.0]
)

# 3. Vision Gate Glare Ratio Histogram
VISION_GLARE_RATIO = Histogram(
    "sevadristi_vision_glare_ratio",
    "HSV glare ratio distribution",
    buckets=[0.01, 0.03, 0.05, 0.08, 0.12, 0.15, 0.25, 0.50]
)

# 4. Indic Name Reconciliation Score Histogram
RECONCILER_SCORE = Histogram(
    "sevadristi_reconciler_composite_score",
    "Indic name matching composite similarity score",
    buckets=[0.2, 0.4, 0.6, 0.7, 0.8, 0.85, 0.9, 0.92, 0.95, 1.0]
)

# 5. Verification Counts
VERIFICATIONS_TOTAL = Counter(
    "sevadristi_verifications_total",
    "Total document verifications conducted",
    ["status", "scheme_id", "processing_mode"]
)

# 6. QR Bridge Operations
QR_OPERATIONS_TOTAL = Counter(
    "sevadristi_qr_operations_total",
    "Total QR encode and decode operations",
    ["operation", "status"]
)

def get_metrics_payload() -> tuple[bytes, str]:
    """Returns raw Prometheus metrics byte stream and content type."""
    return generate_latest(), CONTENT_TYPE_LATEST
