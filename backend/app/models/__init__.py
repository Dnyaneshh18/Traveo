"""ORM model registry – importing this package registers every table on `Base.metadata`."""

from app.models.enums import *  # noqa: F401,F403
from app.models.identity import (  # noqa: F401
    College,
    DriverProfile,
    OtpCode,
    RefreshToken,
    StudentProfile,
    User,
    Vehicle,
)
from app.models.rides import (  # noqa: F401
    DriverOffer,
    HiddenRequest,
    Notification,
    Payment,
    Rating,
    Ride,
    RideEvent,
    RideMember,
    RideRequest,
    SystemConfig,
)
