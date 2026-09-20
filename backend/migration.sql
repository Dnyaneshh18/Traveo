python.exe : INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
At line:1 char:1
+ & ".venv\Scripts\python.exe" -m alembic upgrade head --sql 2>&1 | Out ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (INFO  [alembic....PostgresqlImpl.:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
INFO  [alembic.runtime.migration] Generating static SQL
INFO  [alembic.runtime.migration] Will assume transactional DDL.
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INFO  [alembic.runtime.migration] Running upgrade  -> 69b06206a342, Initial Traveo Schema
-- Running upgrade  -> 69b06206a342

CREATE TABLE daily_statistics (
    id UUID NOT NULL, 
    date TIMESTAMP WITH TIME ZONE NOT NULL, 
    total_rides INTEGER NOT NULL, 
    completed_rides INTEGER NOT NULL, 
    cancelled_rides INTEGER NOT NULL, 
    total_revenue FLOAT NOT NULL, 
    average_occupancy FLOAT NOT NULL, 
    average_wait_seconds FLOAT NOT NULL, 
    active_passengers INTEGER NOT NULL, 
    active_drivers INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_daily_statistics_date ON daily_statistics (date);

CREATE TABLE error_logs (
    id UUID NOT NULL, 
    service VARCHAR(100) NOT NULL, 
    error_type VARCHAR(100) NOT NULL, 
    message TEXT NOT NULL, 
    stack_trace TEXT, 
    request_id VARCHAR(100), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TYPE user_role AS ENUM ('PASSENGER', 'DRIVER', 'ADMIN', 'SUPER_ADMIN', 'SUPPORT', 'FINANCE', 'OPERATIONS');

CREATE TABLE users (
    id UUID NOT NULL, 
    email VARCHAR(255), 
    phone VARCHAR(20), 
    role user_role NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    is_verified BOOLEAN NOT NULL, 
    profile_completed BOOLEAN NOT NULL, 
    last_login TIMESTAMP WITH TIME ZONE, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE UNIQUE INDEX ix_users_phone ON users (phone);

CREATE INDEX ix_users_role ON users (role);

CREATE TABLE admin_profiles (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    department VARCHAR(100), 
    permissions TEXT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    UNIQUE (user_id)
);

CREATE TABLE audit_logs (
    id UUID NOT NULL, 
    user_id UUID, 
    action VARCHAR(100) NOT NULL, 
    entity VARCHAR(100), 
    entity_id VARCHAR(100), 
    old_value TEXT, 
    new_value TEXT, 
    ip_address VARCHAR(50), 
    device VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX idx_audit_user_created ON audit_logs (user_id, created_at);

CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);

CREATE TABLE driver_locations (
    id UUID NOT NULL, 
    driver_id UUID NOT NULL, 
    latitude FLOAT NOT NULL, 
    longitude FLOAT NOT NULL, 
    heading FLOAT, 
    speed FLOAT, 
    accuracy FLOAT, 
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(driver_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_driver_locations_driver_id ON driver_locations (driver_id);

CREATE TYPE verification_status_type AS ENUM ('PENDING', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'EXPIRED');

CREATE TYPE online_status_type AS ENUM ('ONLINE', 'OFFLINE', 'BUSY');

CREATE TABLE driver_profiles (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    first_name VARCHAR(100) NOT NULL, 
    last_name VARCHAR(100), 
    license_number VARCHAR(50), 
    license_expiry TIMESTAMP WITH TIME ZONE, 
    aadhaar_number VARCHAR(50), 
    pan_number VARCHAR(20), 
    profile_photo VARCHAR(500), 
    driver_rating FLOAT NOT NULL, 
    completed_rides INTEGER NOT NULL, 
    cancelled_rides INTEGER NOT NULL, 
    verification_status verification_status_type NOT NULL, 
    online_status online_status_type NOT NULL, 
    current_latitude FLOAT, 
    current_longitude FLOAT, 
    preferred_language VARCHAR(10) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT chk_driver_rating CHECK (driver_rating >= 0 AND driver_rating <= 5), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    UNIQUE (license_number), 
    UNIQUE (user_id)
);

CREATE INDEX ix_driver_profiles_online_status ON driver_profiles (online_status);

CREATE INDEX ix_driver_profiles_verification_status ON driver_profiles (verification_status);

CREATE TYPE notification_type_enum AS ENUM ('RIDE', 'PAYMENT', 'PROMOTION', 'SUPPORT', 'SYSTEM', 'SECURITY', 'WALLET');

CREATE TABLE notifications (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    message TEXT NOT NULL, 
    type notification_type_enum NOT NULL, 
    is_read BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_user_read ON notifications (user_id, is_read);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE TABLE passenger_locations (
    id UUID NOT NULL, 
    passenger_id UUID NOT NULL, 
    latitude FLOAT NOT NULL, 
    longitude FLOAT NOT NULL, 
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(passenger_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_passenger_locations_passenger_id ON passenger_locations (passenger_id);

CREATE TYPE gender_type AS ENUM ('MALE', 'FEMALE', 'OTHER', 'PREFER_NOT_TO_SAY');

CREATE TABLE passenger_profiles (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    first_name VARCHAR(100) NOT NULL, 
    last_name VARCHAR(100), 
    gender gender_type, 
    date_of_birth TIMESTAMP WITH TIME ZONE, 
    profile_photo VARCHAR(500), 
    home_location TEXT, 
    work_location TEXT, 
    preferred_language VARCHAR(10) NOT NULL, 
    average_rating FLOAT NOT NULL, 
    completed_rides INTEGER NOT NULL, 
    cancelled_rides INTEGER NOT NULL, 
    emergency_contact VARCHAR(20), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT chk_passenger_rating CHECK (average_rating >= 0 AND average_rating <= 5), 
    CONSTRAINT chk_passenger_cancelled CHECK (cancelled_rides >= 0), 
    CONSTRAINT chk_passenger_completed CHECK (completed_rides >= 0), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    UNIQUE (user_id)
);

CREATE TYPE group_status_type AS ENUM ('FORMING', 'WAITING_FOR_VOTE', 'VOTING', 'FINALIZED', 'SEARCHING_DRIVER', 'DRIVER_ASSIGNED', 'LOCKED', 'CANCELLED');

CREATE TABLE ride_groups (
    id UUID NOT NULL, 
    group_status group_status_type NOT NULL, 
    maximum_capacity INTEGER NOT NULL, 
    current_passengers INTEGER NOT NULL, 
    estimated_fare FLOAT, 
    driver_id UUID, 
    common_otp VARCHAR(10), 
    search_radius FLOAT, 
    matching_completed BOOLEAN NOT NULL, 
    group_locked BOOLEAN NOT NULL, 
    pickup_sequence_generated BOOLEAN NOT NULL, 
    drop_sequence_generated BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(driver_id) REFERENCES users (id)
);

CREATE INDEX ix_ride_groups_driver_id ON ride_groups (driver_id);

CREATE INDEX ix_ride_groups_group_status ON ride_groups (group_status);

CREATE TYPE ride_type_enum AS ENUM ('SHARED', 'SOLO', 'RENTAL', 'AIRPORT', 'INTERCITY');

CREATE TYPE ride_request_status_type AS ENUM ('PENDING', 'MATCHING', 'MATCHED', 'CANCELLED', 'EXPIRED');

CREATE TABLE ride_requests (
    id UUID NOT NULL, 
    passenger_id UUID NOT NULL, 
    pickup_latitude FLOAT NOT NULL, 
    pickup_longitude FLOAT NOT NULL, 
    pickup_address TEXT, 
    destination_latitude FLOAT NOT NULL, 
    destination_longitude FLOAT NOT NULL, 
    destination_address TEXT, 
    requested_seats INTEGER NOT NULL, 
    ride_type ride_type_enum NOT NULL, 
    status ride_request_status_type NOT NULL, 
    estimated_fare FLOAT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT chk_requested_seats CHECK (requested_seats > 0 AND requested_seats <= 6), 
    FOREIGN KEY(passenger_id) REFERENCES users (id)
);

CREATE INDEX idx_ride_requests_status_created ON ride_requests (status, created_at);

CREATE INDEX ix_ride_requests_passenger_id ON ride_requests (passenger_id);

CREATE INDEX ix_ride_requests_status ON ride_requests (status);

CREATE TABLE saved_places (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    title VARCHAR(100) NOT NULL, 
    address TEXT NOT NULL, 
    latitude FLOAT NOT NULL, 
    longitude FLOAT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_saved_places_user_id ON saved_places (user_id);

CREATE TABLE system_configuration (
    id UUID NOT NULL, 
    key VARCHAR(100) NOT NULL, 
    value TEXT NOT NULL, 
    description TEXT, 
    updated_by UUID, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(updated_by) REFERENCES users (id)
);

CREATE UNIQUE INDEX ix_system_configuration_key ON system_configuration (key);

CREATE TABLE wallets (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    balance FLOAT NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT chk_wallet_balance CHECK (balance >= 0), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    UNIQUE (user_id)
);

CREATE TYPE driver_assignment_status_type AS ENUM ('PENDING', 'ACCEPTED', 'REJECTED', 'TIMED_OUT', 'CANCELLED');

CREATE TABLE driver_assignments (
    id UUID NOT NULL, 
    ride_group_id UUID NOT NULL, 
    driver_id UUID NOT NULL, 
    status driver_assignment_status_type NOT NULL, 
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    accepted_at TIMESTAMP WITH TIME ZONE, 
    rejected_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(driver_id) REFERENCES users (id), 
    FOREIGN KEY(ride_group_id) REFERENCES ride_groups (id)
);

CREATE INDEX ix_driver_assignments_driver_id ON driver_assignments (driver_id);

CREATE INDEX ix_driver_assignments_ride_group_id ON driver_assignments (ride_group_id);

CREATE TYPE vote_choice_type AS ENUM ('CONTINUE', 'WAIT', 'CANCEL');

CREATE TABLE group_votes (
    id UUID NOT NULL, 
    group_id UUID NOT NULL, 
    passenger_id UUID NOT NULL, 
    vote vote_choice_type NOT NULL, 
    voted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(group_id) REFERENCES ride_groups (id) ON DELETE CASCADE, 
    FOREIGN KEY(passenger_id) REFERENCES users (id), 
    CONSTRAINT uq_group_vote UNIQUE (group_id, passenger_id)
);

CREATE INDEX ix_group_votes_group_id ON group_votes (group_id);

CREATE TABLE matching_sessions (
    id UUID NOT NULL, 
    ride_request_id UUID NOT NULL, 
    matching_radius FLOAT NOT NULL, 
    matching_status VARCHAR(30) NOT NULL, 
    timer_started TIMESTAMP WITH TIME ZONE, 
    timer_expired TIMESTAMP WITH TIME ZONE, 
    matched_count INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ride_request_id) REFERENCES ride_requests (id)
);

CREATE INDEX ix_matching_sessions_ride_request_id ON matching_sessions (ride_request_id);

CREATE TYPE boarding_status_type AS ENUM ('WAITING', 'BOARDED', 'NO_SHOW', 'CANCELLED');

CREATE TYPE drop_status_type AS ENUM ('PENDING', 'DROPPED', 'CANCELLED');

CREATE TABLE ride_group_members (
    id UUID NOT NULL, 
    group_id UUID NOT NULL, 
    passenger_id UUID NOT NULL, 
    ride_request_id UUID, 
    pickup_order INTEGER, 
    drop_order INTEGER, 
    boarding_status boarding_status_type NOT NULL, 
    drop_status drop_status_type NOT NULL, 
    joined_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(group_id) REFERENCES ride_groups (id) ON DELETE CASCADE, 
    FOREIGN KEY(passenger_id) REFERENCES users (id), 
    FOREIGN KEY(ride_request_id) REFERENCES ride_requests (id), 
    CONSTRAINT uq_group_passenger UNIQUE (group_id, passenger_id)
);

CREATE INDEX ix_ride_group_members_group_id ON ride_group_members (group_id);

CREATE INDEX ix_ride_group_members_passenger_id ON ride_group_members (passenger_id);

CREATE TYPE message_type_enum AS ENUM ('TEXT', 'EMOJI', 'SYSTEM', 'IMAGE', 'LOCATION');

CREATE TABLE ride_messages (
    id UUID NOT NULL, 
    ride_group_id UUID NOT NULL, 
    sender_id UUID NOT NULL, 
    message TEXT NOT NULL, 
    message_type message_type_enum NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ride_group_id) REFERENCES ride_groups (id) ON DELETE CASCADE, 
    FOREIGN KEY(sender_id) REFERENCES users (id)
);

CREATE INDEX ix_ride_messages_ride_group_id ON ride_messages (ride_group_id);

CREATE TABLE ride_otps (
    id UUID NOT NULL, 
    ride_group_id UUID NOT NULL, 
    otp VARCHAR(10) NOT NULL, 
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    verified BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ride_group_id) REFERENCES ride_groups (id)
);

CREATE INDEX ix_ride_otps_ride_group_id ON ride_otps (ride_group_id);

CREATE TYPE ride_status_type AS ENUM ('REQUEST_CREATED', 'SEARCHING_PASSENGERS', 'GROUP_FORMING', 'WAITING_FOR_VOTE', 'SEARCHING_DRIVER', 'DRIVER_ASSIGNED', 'OTP_GENERATED', 'DRIVER_EN_ROUTE', 'PICKUP_IN_PROGRESS', 'ALL_PASSENGERS_BOARDED', 'RIDE_STARTED', 'DROP_IN_PROGRESS', 'RIDE_COMPLETED', 'PAYMENT_COMPLETED', 'RATING_PENDING', 'RATING_COMPLETED', 'PASSENGER_CANCELLED', 'DRIVER_CANCELLED', 'GROUP_CANCELLED', 'MATCHING_FAILED', 'NO_DRIVER_FOUND', 'PAYMENT_FAILED', 'REFUND_INITIATED');

CREATE TABLE rides (
    id UUID NOT NULL, 
    ride_group_id UUID NOT NULL, 
    driver_id UUID NOT NULL, 
    ride_status ride_status_type NOT NULL, 
    ride_started TIMESTAMP WITH TIME ZONE, 
    ride_completed TIMESTAMP WITH TIME ZONE, 
    actual_distance FLOAT, 
    actual_duration FLOAT, 
    total_fare FLOAT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(driver_id) REFERENCES users (id), 
    FOREIGN KEY(ride_group_id) REFERENCES ride_groups (id)
);

CREATE INDEX idx_rides_driver_status ON rides (driver_id, ride_status);

CREATE INDEX ix_rides_driver_id ON rides (driver_id);

CREATE INDEX ix_rides_ride_group_id ON rides (ride_group_id);

CREATE INDEX ix_rides_ride_status ON rides (ride_status);

CREATE TYPE vehicle_status_type AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED');

CREATE TABLE vehicles (
    id UUID NOT NULL, 
    driver_id UUID NOT NULL, 
    vehicle_type VARCHAR(50) NOT NULL, 
    vehicle_brand VARCHAR(100), 
    vehicle_model VARCHAR(100), 
    vehicle_color VARCHAR(50), 
    registration_number VARCHAR(30) NOT NULL, 
    seat_capacity INTEGER NOT NULL, 
    insurance_number VARCHAR(100), 
    insurance_expiry TIMESTAMP WITH TIME ZONE, 
    pollution_certificate VARCHAR(500), 
    registration_document VARCHAR(500), 
    vehicle_photo VARCHAR(500), 
    status vehicle_status_type NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT chk_seat_capacity CHECK (seat_capacity > 0), 
    FOREIGN KEY(driver_id) REFERENCES driver_profiles (id) ON DELETE CASCADE, 
    UNIQUE (registration_number)
);

CREATE INDEX ix_vehicles_driver_id ON vehicles (driver_id);

CREATE TYPE wallet_tx_type AS ENUM ('CREDIT', 'DEBIT', 'REFUND', 'PROMOTION', 'RIDE_PAYMENT', 'PAYOUT', 'ADJUSTMENT');

CREATE TABLE wallet_transactions (
    id UUID NOT NULL, 
    wallet_id UUID NOT NULL, 
    type wallet_tx_type NOT NULL, 
    amount FLOAT NOT NULL, 
    description TEXT, 
    reference VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(wallet_id) REFERENCES wallets (id) ON DELETE CASCADE
);

CREATE INDEX ix_wallet_transactions_wallet_id ON wallet_transactions (wallet_id);

CREATE TYPE payout_status_type AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');

CREATE TABLE driver_payouts (
    id UUID NOT NULL, 
    driver_id UUID NOT NULL, 
    ride_id UUID NOT NULL, 
    gross_amount FLOAT NOT NULL, 
    commission FLOAT NOT NULL, 
    net_amount FLOAT NOT NULL, 
    status payout_status_type NOT NULL, 
    paid_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(driver_id) REFERENCES users (id), 
    FOREIGN KEY(ride_id) REFERENCES rides (id)
);

CREATE INDEX ix_driver_payouts_driver_id ON driver_payouts (driver_id);

CREATE TABLE drop_events (
    id UUID NOT NULL, 
    ride_id UUID NOT NULL, 
    passenger_id UUID NOT NULL, 
    drop_time TIMESTAMP WITH TIME ZONE NOT NULL, 
    completed BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(passenger_id) REFERENCES users (id), 
    FOREIGN KEY(ride_id) REFERENCES rides (id)
);

CREATE INDEX ix_drop_events_ride_id ON drop_events (ride_id);

CREATE TYPE payment_method_type AS ENUM ('UPI', 'CARD', 'WALLET', 'CASH', 'NET_BANKING');

CREATE TYPE payment_status_type AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED');

CREATE TABLE payments (
    id UUID NOT NULL, 
    ride_id UUID NOT NULL, 
    payer_id UUID NOT NULL, 
    amount FLOAT NOT NULL, 
    method payment_method_type, 
    status payment_status_type NOT NULL, 
    transaction_reference VARCHAR(255), 
    idempotency_key VARCHAR(255), 
    payment_time TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT chk_payment_amount CHECK (amount >= 0), 
    FOREIGN KEY(payer_id) REFERENCES users (id), 
    FOREIGN KEY(ride_id) REFERENCES rides (id), 
    UNIQUE (idempotency_key), 
    UNIQUE (transaction_reference)
);

CREATE INDEX ix_payments_payer_id ON payments (payer_id);

CREATE INDEX ix_payments_ride_id ON payments (ride_id);

CREATE INDEX ix_payments_status ON payments (status);

CREATE TABLE pickup_events (
    id UUID NOT NULL, 
    ride_id UUID NOT NULL, 
    passenger_id UUID NOT NULL, 
    pickup_time TIMESTAMP WITH TIME ZONE NOT NULL, 
    verified BOOLEAN NOT NULL, 
    no_show BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(passenger_id) REFERENCES users (id), 
    FOREIGN KEY(ride_id) REFERENCES rides (id)
);

CREATE INDEX ix_pickup_events_ride_id ON pickup_events (ride_id);

CREATE TABLE ratings (
    id UUID NOT NULL, 
    ride_id UUID NOT NULL, 
    rater_id UUID NOT NULL, 
    rated_id UUID NOT NULL, 
    rating INTEGER NOT NULL, 
    review TEXT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT chk_rating_range CHECK (rating >= 1 AND rating <= 5), 
    FOREIGN KEY(rated_id) REFERENCES users (id), 
    FOREIGN KEY(rater_id) REFERENCES users (id), 
    FOREIGN KEY(ride_id) REFERENCES rides (id), 
    CONSTRAINT uq_ride_rating UNIQUE (ride_id, rater_id, rated_id)
);

CREATE INDEX ix_ratings_ride_id ON ratings (ride_id);

CREATE TABLE ride_statistics (
    id UUID NOT NULL, 
    ride_id UUID NOT NULL, 
    matching_duration_seconds FLOAT, 
    driver_assignment_seconds FLOAT, 
    total_pickup_seconds FLOAT, 
    total_ride_seconds FLOAT, 
    occupancy INTEGER, 
    route_efficiency FLOAT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ride_id) REFERENCES rides (id)
);

CREATE INDEX ix_ride_statistics_ride_id ON ride_statistics (ride_id);

CREATE TYPE support_status_type AS ENUM ('OPEN', 'ASSIGNED', 'WAITING_USER', 'RESOLVED', 'CLOSED');

CREATE TABLE support_tickets (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    category VARCHAR(100) NOT NULL, 
    description TEXT NOT NULL, 
    status support_status_type NOT NULL, 
    assigned_to UUID, 
    ride_id UUID, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(assigned_to) REFERENCES users (id), 
    FOREIGN KEY(ride_id) REFERENCES rides (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_support_tickets_status ON support_tickets (status);

CREATE INDEX ix_support_tickets_user_id ON support_tickets (user_id);

CREATE TYPE refund_status_type AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');

CREATE TABLE refunds (
    id UUID NOT NULL, 
    payment_id UUID NOT NULL, 
    amount FLOAT NOT NULL, 
    reason TEXT, 
    status refund_status_type NOT NULL, 
    processed_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(payment_id) REFERENCES payments (id)
);

CREATE INDEX ix_refunds_payment_id ON refunds (payment_id);

INSERT INTO alembic_version (version_num) VALUES ('69b06206a342') RETURNING alembic_version.version_num;

COMMIT;

