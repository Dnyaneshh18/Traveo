"""
Traveo Shared — Constants

Application-wide constants shared between backend and potential future modules.
These are NOT configurable at runtime — use system_configuration for runtime values.
"""

# ── Ride Lifecycle ───────────────────────────────────────────
MIN_PASSENGERS_FOR_GROUP = 2
MAX_PASSENGERS_PER_GROUP = 4
MAX_SEATS_PER_REQUEST = 6
OTP_LENGTH = 4
AUTH_OTP_LENGTH = 6

# ── API ──────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
API_VERSION = "v1"

# ── File Uploads ─────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = 10
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}

# ── Supabase Storage Buckets ────────────────────────────────
BUCKET_PROFILE_PHOTOS = "profile-photos"
BUCKET_DRIVER_DOCUMENTS = "driver-documents"
BUCKET_VEHICLE_IMAGES = "vehicle-images"
BUCKET_SUPPORT_ATTACHMENTS = "support-attachments"

# ── Currency ─────────────────────────────────────────────────
DEFAULT_CURRENCY = "INR"

# ── Ride Status Groups (for filtering) ──────────────────────
ACTIVE_RIDE_STATUSES = {
    "request_created",
    "searching_passengers",
    "group_forming",
    "waiting_for_vote",
    "searching_driver",
    "driver_assigned",
    "otp_generated",
    "driver_en_route",
    "pickup_in_progress",
    "all_passengers_boarded",
    "ride_started",
    "drop_in_progress",
}

COMPLETED_RIDE_STATUSES = {
    "ride_completed",
    "payment_completed",
    "rating_pending",
    "rating_completed",
}

CANCELLED_RIDE_STATUSES = {
    "passenger_cancelled",
    "driver_cancelled",
    "group_cancelled",
    "matching_failed",
    "no_driver_found",
}
