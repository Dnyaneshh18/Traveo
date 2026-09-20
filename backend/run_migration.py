"""
Direct migration script — creates all Traveo tables via raw SQL using asyncpg.
Bypasses Alembic's async engine issues.
"""
import asyncio
import asyncpg

DDL = """
-- ========================================
-- Enums
-- ========================================
DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('PASSENGER','DRIVER','ADMIN','SUPER_ADMIN','SUPPORT','FINANCE','OPERATIONS');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE verification_status_type AS ENUM ('PENDING','SUBMITTED','UNDER_REVIEW','APPROVED','REJECTED','EXPIRED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE online_status_type AS ENUM ('ONLINE','OFFLINE','BUSY');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE gender_type AS ENUM ('MALE','FEMALE','OTHER','PREFER_NOT_TO_SAY');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE group_status_type AS ENUM ('FORMING','WAITING_FOR_VOTE','VOTING','FINALIZED','SEARCHING_DRIVER','DRIVER_ASSIGNED','LOCKED','CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE ride_request_status_type AS ENUM ('PENDING','MATCHING','MATCHED','CANCELLED','EXPIRED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE ride_type_enum AS ENUM ('SHARED','SOLO','RENTAL','AIRPORT','INTERCITY');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE driver_assignment_status_type AS ENUM ('PENDING','ACCEPTED','REJECTED','TIMED_OUT','CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE vote_choice_type AS ENUM ('CONTINUE','WAIT','CANCEL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE boarding_status_type AS ENUM ('WAITING','BOARDED','NO_SHOW','CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE drop_status_type AS ENUM ('PENDING','DROPPED','CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE ride_status_type AS ENUM ('REQUEST_CREATED','SEARCHING_PASSENGERS','GROUP_FORMING','WAITING_FOR_VOTE','SEARCHING_DRIVER','DRIVER_ASSIGNED','OTP_GENERATED','DRIVER_EN_ROUTE','PICKUP_IN_PROGRESS','ALL_PASSENGERS_BOARDED','RIDE_STARTED','DROP_IN_PROGRESS','RIDE_COMPLETED','PAYMENT_COMPLETED','RATING_PENDING','RATING_COMPLETED','PASSENGER_CANCELLED','DRIVER_CANCELLED','GROUP_CANCELLED','MATCHING_FAILED','NO_DRIVER_FOUND','PAYMENT_FAILED','REFUND_INITIATED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE notification_type_enum AS ENUM ('RIDE','PAYMENT','PROMOTION','SUPPORT','SYSTEM','SECURITY','WALLET');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE message_type_enum AS ENUM ('TEXT','EMOJI','SYSTEM','IMAGE','LOCATION');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE payment_method_type AS ENUM ('UPI','CARD','WALLET','CASH','NET_BANKING');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE payment_status_type AS ENUM ('PENDING','PROCESSING','COMPLETED','FAILED','REFUNDED','PARTIALLY_REFUNDED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE wallet_tx_type AS ENUM ('CREDIT','DEBIT','REFUND','PROMOTION','RIDE_PAYMENT','PAYOUT','ADJUSTMENT');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE vehicle_status_type AS ENUM ('PENDING','APPROVED','REJECTED','SUSPENDED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE payout_status_type AS ENUM ('PENDING','PROCESSING','COMPLETED','FAILED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE support_status_type AS ENUM ('OPEN','ASSIGNED','WAITING_USER','RESOLVED','CLOSED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE refund_status_type AS ENUM ('PENDING','PROCESSING','COMPLETED','FAILED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ========================================
-- Tables (no FK dependencies)
-- ========================================

CREATE TABLE IF NOT EXISTS daily_statistics (
    id UUID PRIMARY KEY,
    date TIMESTAMPTZ NOT NULL,
    total_rides INTEGER NOT NULL,
    completed_rides INTEGER NOT NULL,
    cancelled_rides INTEGER NOT NULL,
    total_revenue FLOAT NOT NULL,
    average_occupancy FLOAT NOT NULL,
    average_wait_seconds FLOAT NOT NULL,
    active_passengers INTEGER NOT NULL,
    active_drivers INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_daily_statistics_date ON daily_statistics(date);

CREATE TABLE IF NOT EXISTS error_logs (
    id UUID PRIMARY KEY,
    service VARCHAR(100) NOT NULL,
    error_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    stack_trace TEXT,
    request_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255),
    phone VARCHAR(20),
    role user_role NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    profile_completed BOOLEAN NOT NULL DEFAULT FALSE,
    last_login TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS ix_users_role ON users(role);

-- ========================================
-- Tables depending on users
-- ========================================

CREATE TABLE IF NOT EXISTS admin_profiles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    department VARCHAR(100),
    permissions TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity VARCHAR(100),
    entity_id VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(50),
    device VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_user_created ON audit_logs(user_id, created_at);

CREATE TABLE IF NOT EXISTS driver_locations (
    id UUID PRIMARY KEY,
    driver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    heading FLOAT,
    speed FLOAT,
    accuracy FLOAT,
    timestamp TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_driver_locations_driver_id ON driver_locations(driver_id);

CREATE TABLE IF NOT EXISTS driver_profiles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    license_number VARCHAR(50) UNIQUE,
    license_expiry TIMESTAMPTZ,
    aadhaar_number VARCHAR(50),
    pan_number VARCHAR(20),
    profile_photo VARCHAR(500),
    driver_rating FLOAT NOT NULL DEFAULT 0 CHECK (driver_rating >= 0 AND driver_rating <= 5),
    completed_rides INTEGER NOT NULL DEFAULT 0,
    cancelled_rides INTEGER NOT NULL DEFAULT 0,
    verification_status verification_status_type NOT NULL DEFAULT 'PENDING',
    online_status online_status_type NOT NULL DEFAULT 'OFFLINE',
    current_latitude FLOAT,
    current_longitude FLOAT,
    preferred_language VARCHAR(10) NOT NULL DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_driver_profiles_online_status ON driver_profiles(online_status);
CREATE INDEX IF NOT EXISTS ix_driver_profiles_verification_status ON driver_profiles(verification_status);

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type notification_type_enum NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);

CREATE TABLE IF NOT EXISTS passenger_locations (
    id UUID PRIMARY KEY,
    passenger_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_passenger_locations_passenger_id ON passenger_locations(passenger_id);

CREATE TABLE IF NOT EXISTS passenger_profiles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    gender gender_type,
    date_of_birth TIMESTAMPTZ,
    profile_photo VARCHAR(500),
    home_location TEXT,
    work_location TEXT,
    preferred_language VARCHAR(10) NOT NULL DEFAULT 'en',
    average_rating FLOAT NOT NULL DEFAULT 0 CHECK (average_rating >= 0 AND average_rating <= 5),
    completed_rides INTEGER NOT NULL DEFAULT 0 CHECK (completed_rides >= 0),
    cancelled_rides INTEGER NOT NULL DEFAULT 0 CHECK (cancelled_rides >= 0),
    emergency_contact VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS ride_groups (
    id UUID PRIMARY KEY,
    group_status group_status_type NOT NULL DEFAULT 'FORMING',
    maximum_capacity INTEGER NOT NULL DEFAULT 4,
    current_passengers INTEGER NOT NULL DEFAULT 0,
    estimated_fare FLOAT,
    driver_id UUID REFERENCES users(id),
    common_otp VARCHAR(10),
    search_radius FLOAT,
    matching_completed BOOLEAN NOT NULL DEFAULT FALSE,
    group_locked BOOLEAN NOT NULL DEFAULT FALSE,
    pickup_sequence_generated BOOLEAN NOT NULL DEFAULT FALSE,
    drop_sequence_generated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ride_groups_driver_id ON ride_groups(driver_id);
CREATE INDEX IF NOT EXISTS ix_ride_groups_group_status ON ride_groups(group_status);

CREATE TABLE IF NOT EXISTS ride_requests (
    id UUID PRIMARY KEY,
    passenger_id UUID NOT NULL REFERENCES users(id),
    pickup_latitude FLOAT NOT NULL,
    pickup_longitude FLOAT NOT NULL,
    pickup_address TEXT,
    destination_latitude FLOAT NOT NULL,
    destination_longitude FLOAT NOT NULL,
    destination_address TEXT,
    requested_seats INTEGER NOT NULL CHECK (requested_seats > 0 AND requested_seats <= 6),
    ride_type ride_type_enum NOT NULL DEFAULT 'SHARED',
    status ride_request_status_type NOT NULL DEFAULT 'PENDING',
    estimated_fare FLOAT,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ride_requests_passenger_id ON ride_requests(passenger_id);
CREATE INDEX IF NOT EXISTS ix_ride_requests_status ON ride_requests(status);
CREATE INDEX IF NOT EXISTS idx_ride_requests_status_created ON ride_requests(status, created_at);

CREATE TABLE IF NOT EXISTS saved_places (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_saved_places_user_id ON saved_places(user_id);

CREATE TABLE IF NOT EXISTS system_configuration (
    id UUID PRIMARY KEY,
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_system_configuration_key ON system_configuration(key);

CREATE TABLE IF NOT EXISTS wallets (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    balance FLOAT NOT NULL DEFAULT 0 CHECK (balance >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    updated_at TIMESTAMPTZ NOT NULL
);

-- ========================================
-- Tables depending on ride_groups / ride_requests
-- ========================================

CREATE TABLE IF NOT EXISTS driver_assignments (
    id UUID PRIMARY KEY,
    ride_group_id UUID NOT NULL REFERENCES ride_groups(id),
    driver_id UUID NOT NULL REFERENCES users(id),
    status driver_assignment_status_type NOT NULL DEFAULT 'PENDING',
    assigned_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    rejected_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_driver_assignments_driver_id ON driver_assignments(driver_id);
CREATE INDEX IF NOT EXISTS ix_driver_assignments_ride_group_id ON driver_assignments(ride_group_id);

CREATE TABLE IF NOT EXISTS group_votes (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES ride_groups(id) ON DELETE CASCADE,
    passenger_id UUID NOT NULL REFERENCES users(id),
    vote vote_choice_type NOT NULL,
    voted_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_group_vote UNIQUE (group_id, passenger_id)
);
CREATE INDEX IF NOT EXISTS ix_group_votes_group_id ON group_votes(group_id);

CREATE TABLE IF NOT EXISTS matching_sessions (
    id UUID PRIMARY KEY,
    ride_request_id UUID NOT NULL REFERENCES ride_requests(id),
    matching_radius FLOAT NOT NULL,
    matching_status VARCHAR(30) NOT NULL,
    timer_started TIMESTAMPTZ,
    timer_expired TIMESTAMPTZ,
    matched_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_matching_sessions_ride_request_id ON matching_sessions(ride_request_id);

CREATE TABLE IF NOT EXISTS ride_group_members (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES ride_groups(id) ON DELETE CASCADE,
    passenger_id UUID NOT NULL REFERENCES users(id),
    ride_request_id UUID REFERENCES ride_requests(id),
    pickup_order INTEGER,
    drop_order INTEGER,
    boarding_status boarding_status_type NOT NULL DEFAULT 'WAITING',
    drop_status drop_status_type NOT NULL DEFAULT 'PENDING',
    joined_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_group_passenger UNIQUE (group_id, passenger_id)
);
CREATE INDEX IF NOT EXISTS ix_ride_group_members_group_id ON ride_group_members(group_id);
CREATE INDEX IF NOT EXISTS ix_ride_group_members_passenger_id ON ride_group_members(passenger_id);

CREATE TABLE IF NOT EXISTS ride_messages (
    id UUID PRIMARY KEY,
    ride_group_id UUID NOT NULL REFERENCES ride_groups(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    message_type message_type_enum NOT NULL DEFAULT 'TEXT',
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ride_messages_ride_group_id ON ride_messages(ride_group_id);

CREATE TABLE IF NOT EXISTS ride_otps (
    id UUID PRIMARY KEY,
    ride_group_id UUID NOT NULL REFERENCES ride_groups(id),
    otp VARCHAR(10) NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_ride_otps_ride_group_id ON ride_otps(ride_group_id);

CREATE TABLE IF NOT EXISTS rides (
    id UUID PRIMARY KEY,
    ride_group_id UUID NOT NULL REFERENCES ride_groups(id),
    driver_id UUID NOT NULL REFERENCES users(id),
    ride_status ride_status_type NOT NULL,
    ride_started TIMESTAMPTZ,
    ride_completed TIMESTAMPTZ,
    actual_distance FLOAT,
    actual_duration FLOAT,
    total_fare FLOAT,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_rides_driver_id ON rides(driver_id);
CREATE INDEX IF NOT EXISTS ix_rides_ride_group_id ON rides(ride_group_id);
CREATE INDEX IF NOT EXISTS ix_rides_ride_status ON rides(ride_status);
CREATE INDEX IF NOT EXISTS idx_rides_driver_status ON rides(driver_id, ride_status);

-- ========================================
-- Tables depending on driver_profiles
-- ========================================

CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY,
    driver_id UUID NOT NULL REFERENCES driver_profiles(id) ON DELETE CASCADE,
    vehicle_type VARCHAR(50) NOT NULL,
    vehicle_brand VARCHAR(100),
    vehicle_model VARCHAR(100),
    vehicle_color VARCHAR(50),
    registration_number VARCHAR(30) NOT NULL UNIQUE,
    seat_capacity INTEGER NOT NULL CHECK (seat_capacity > 0),
    insurance_number VARCHAR(100),
    insurance_expiry TIMESTAMPTZ,
    pollution_certificate VARCHAR(500),
    registration_document VARCHAR(500),
    vehicle_photo VARCHAR(500),
    status vehicle_status_type NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_vehicles_driver_id ON vehicles(driver_id);

-- ========================================
-- Tables depending on wallets
-- ========================================

CREATE TABLE IF NOT EXISTS wallet_transactions (
    id UUID PRIMARY KEY,
    wallet_id UUID NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    type wallet_tx_type NOT NULL,
    amount FLOAT NOT NULL,
    description TEXT,
    reference VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_wallet_transactions_wallet_id ON wallet_transactions(wallet_id);

-- ========================================
-- Tables depending on rides
-- ========================================

CREATE TABLE IF NOT EXISTS driver_payouts (
    id UUID PRIMARY KEY,
    driver_id UUID NOT NULL REFERENCES users(id),
    ride_id UUID NOT NULL REFERENCES rides(id),
    gross_amount FLOAT NOT NULL,
    commission FLOAT NOT NULL,
    net_amount FLOAT NOT NULL,
    status payout_status_type NOT NULL DEFAULT 'PENDING',
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_driver_payouts_driver_id ON driver_payouts(driver_id);

CREATE TABLE IF NOT EXISTS drop_events (
    id UUID PRIMARY KEY,
    ride_id UUID NOT NULL REFERENCES rides(id),
    passenger_id UUID NOT NULL REFERENCES users(id),
    drop_time TIMESTAMPTZ NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_drop_events_ride_id ON drop_events(ride_id);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY,
    ride_id UUID NOT NULL REFERENCES rides(id),
    payer_id UUID NOT NULL REFERENCES users(id),
    amount FLOAT NOT NULL CHECK (amount >= 0),
    method payment_method_type,
    status payment_status_type NOT NULL DEFAULT 'PENDING',
    transaction_reference VARCHAR(255) UNIQUE,
    idempotency_key VARCHAR(255) UNIQUE,
    payment_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_payments_payer_id ON payments(payer_id);
CREATE INDEX IF NOT EXISTS ix_payments_ride_id ON payments(ride_id);
CREATE INDEX IF NOT EXISTS ix_payments_status ON payments(status);

CREATE TABLE IF NOT EXISTS pickup_events (
    id UUID PRIMARY KEY,
    ride_id UUID NOT NULL REFERENCES rides(id),
    passenger_id UUID NOT NULL REFERENCES users(id),
    pickup_time TIMESTAMPTZ NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    no_show BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_pickup_events_ride_id ON pickup_events(ride_id);

CREATE TABLE IF NOT EXISTS ratings (
    id UUID PRIMARY KEY,
    ride_id UUID NOT NULL REFERENCES rides(id),
    rater_id UUID NOT NULL REFERENCES users(id),
    rated_id UUID NOT NULL REFERENCES users(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_ride_rating UNIQUE (ride_id, rater_id, rated_id)
);
CREATE INDEX IF NOT EXISTS ix_ratings_ride_id ON ratings(ride_id);

CREATE TABLE IF NOT EXISTS ride_statistics (
    id UUID PRIMARY KEY,
    ride_id UUID NOT NULL REFERENCES rides(id),
    matching_duration_seconds FLOAT,
    driver_assignment_seconds FLOAT,
    total_pickup_seconds FLOAT,
    total_ride_seconds FLOAT,
    occupancy INTEGER,
    route_efficiency FLOAT,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ride_statistics_ride_id ON ride_statistics(ride_id);

CREATE TABLE IF NOT EXISTS support_tickets (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    status support_status_type NOT NULL DEFAULT 'OPEN',
    assigned_to UUID REFERENCES users(id),
    ride_id UUID REFERENCES rides(id),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX IF NOT EXISTS ix_support_tickets_status ON support_tickets(status);

-- ========================================
-- Tables depending on payments
-- ========================================

CREATE TABLE IF NOT EXISTS refunds (
    id UUID PRIMARY KEY,
    payment_id UUID NOT NULL REFERENCES payments(id),
    amount FLOAT NOT NULL,
    reason TEXT,
    status refund_status_type NOT NULL DEFAULT 'PENDING',
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_refunds_payment_id ON refunds(payment_id);

-- ========================================
-- Alembic version tracking
-- ========================================
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
INSERT INTO alembic_version (version_num) VALUES ('69b06206a342')
ON CONFLICT (version_num) DO NOTHING;
"""


async def main():
    print("Connecting to Supabase...")
    conn = await asyncpg.connect(
        host="db.toqvohzccqziphjjsiil.supabase.co",
        port=5432,
        user="postgres",
        password="Nandupatil@123",
        database="postgres",
    )
    print("Connected. Running migration...")
    try:
        await conn.execute(DDL)
        print("[OK] All tables created successfully!")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
    finally:
        # Verify
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
        print(f"\nTables in public schema: {len(tables)}")
        for t in tables:
            print(f"  - {t['table_name']}")
        await conn.close()


asyncio.run(main())
