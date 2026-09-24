
CREATE TABLE colleges (
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	short_name VARCHAR(60), 
	aliases TEXT, 
	institution_type VARCHAR(20) NOT NULL, 
	city VARCHAR(100) NOT NULL, 
	state VARCHAR(100), 
	address TEXT, 
	latitude FLOAT NOT NULL, 
	longitude FLOAT NOT NULL, 
	id_pattern VARCHAR(200), 
	id_hint VARCHAR(200), 
	email_domain VARCHAR(120), 
	is_active BOOLEAN NOT NULL, 
	id VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
)



CREATE TABLE otp_codes (
	phone VARCHAR(20) NOT NULL, 
	code_hash VARCHAR(64) NOT NULL, 
	purpose VARCHAR(20) NOT NULL, 
	attempts INTEGER NOT NULL, 
	consumed BOOLEAN NOT NULL, 
	expires_at DATETIME NOT NULL, 
	created_at DATETIME NOT NULL, 
	id VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id)
)



CREATE TABLE system_config (
	"key" VARCHAR(80) NOT NULL, 
	value TEXT NOT NULL, 
	description VARCHAR(300), 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY ("key")
)



CREATE TABLE users (
	phone VARCHAR(20), 
	email VARCHAR(255), 
	password_hash VARCHAR(255), 
	role VARCHAR(20) NOT NULL, 
	full_name VARCHAR(120) NOT NULL, 
	avatar_url VARCHAR(500), 
	is_active BOOLEAN NOT NULL, 
	profile_completed BOOLEAN NOT NULL, 
	push_token VARCHAR(255), 
	last_login_at DATETIME, 
	id VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
)



CREATE TABLE driver_profiles (
	user_id VARCHAR(32) NOT NULL, 
	license_number VARCHAR(50), 
	license_url VARCHAR(500), 
	verification_status VARCHAR(20) NOT NULL, 
	verification_note TEXT, 
	status VARCHAR(20) NOT NULL, 
	average_rating FLOAT NOT NULL, 
	rating_count INTEGER NOT NULL, 
	completed_rides INTEGER NOT NULL, 
	offers_received INTEGER NOT NULL, 
	offers_accepted INTEGER NOT NULL, 
	total_earnings_inr FLOAT NOT NULL, 
	current_ride_id VARCHAR(32), 
	latitude FLOAT, 
	longitude FLOAT, 
	heading FLOAT, 
	location_updated_at DATETIME, 
	id VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	UNIQUE (license_number)
)



CREATE TABLE notifications (
	user_id VARCHAR(32) NOT NULL, 
	type VARCHAR(10) NOT NULL, 
	title VARCHAR(120) NOT NULL, 
	body VARCHAR(400) NOT NULL, 
	data TEXT, 
	is_read BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	id VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)



CREATE TABLE refresh_tokens (
	user_id VARCHAR(32) NOT NULL, 
	jti VARCHAR(32) NOT NULL, 
	revoked BOOLEAN NOT NULL, 
	expires_at DATETIME NOT NULL, 
	created_at DATETIME NOT NULL, 
	id VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	UNIQUE (jti)
)



CREATE TABLE ride_requests (
	creator_id VARCHAR(32) NOT NULL, 
	college_id VARCHAR(32) NOT NULL, 
	direction VARCHAR(20) NOT NULL, 
	vehicle_type VARCHAR(20) NOT NULL, 
	seat_capacity INTEGER NOT NULL, 
	seats_taken INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	origin_lat FLOAT NOT NULL, 
	origin_lng FLOAT NOT NULL, 
	origin_address TEXT NOT NULL, 
	destination_lat FLOAT NOT NULL, 
	destination_lng FLOAT NOT NULL, 
	destination_address TEXT NOT NULL, 
	departure_at DATETIME NOT NULL, 
	expires_at DATETIME NOT NULL, 
	note VARCHAR(200), 
	women_only BOOLEAN NOT NULL, 
	route_polyline TEXT, 
	route_distance_km FLOAT, 
	route_duration_min FLOAT, 
	estimated_fare_total FLOAT, 
	estimated_fare_solo FLOAT, 
	otp_hash VARCHAR(64), 
	otp_plain VARCHAR(8), 
	locked_at DATETIME, 
	dispatch_started_at DATETIME, 
	dispatch_radius_km FLOAT, 
	dispatch_attempts INTEGER NOT NULL, 
	cancel_reason VARCHAR(200), 
	id VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(creator_id) REFERENCES users (id), 
	FOREIGN KEY(college_id) REFERENCES colleges (id)
)



CREATE TABLE student_profiles (
	user_id VARCHAR(32) NOT NULL, 
	college_id VARCHAR(32) NOT NULL, 
	college_id_number VARCHAR(60) NOT NULL, 
	college_name_on_id VARCHAR(200) NOT NULL, 
	identity_match_score FLOAT NOT NULL, 
	id_card_url VARCHAR(500), 
	gender VARCHAR(10), 
	course VARCHAR(120), 
	graduation_year INTEGER, 
	emergency_contact VARCHAR(20), 
	verification_status VARCHAR(20) NOT NULL, 
	verification_note TEXT, 
	verified_at DATETIME, 
	average_rating FLOAT NOT NULL, 
	rating_count INTEGER NOT NULL, 
	completed_rides INTEGER NOT NULL, 
	cancelled_rides INTEGER NOT NULL, 
	total_saved_inr FLOAT NOT NULL, 
	id VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_student_identity UNIQUE (college_id, college_id_number), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(college_id) REFERENCES colleges (id)
)



CREATE TABLE driver_offers (
	request_id VARCHAR(32) NOT NULL, 
	driver_user_id VARCHAR(32) NOT NULL, 
	status VARCHAR(12) NOT NULL, 
	radius_km FLOAT NOT NULL, 
	distance_km FLOAT NOT NULL, 
	eta_min FLOAT NOT NULL, 
	score FLOAT NOT NULL, 
	driver_payout_inr FLOAT, 
	created_at DATETIME NOT NULL, 
	expires_at DATETIME NOT NULL, 
	responded_at DATETIME, 
	id VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(request_id) REFERENCES ride_requests (id), 
	FOREIGN KEY(driver_user_id) REFERENCES users (id)
)



CREATE TABLE hidden_requests (
	request_id VARCHAR(32) NOT NULL, 
	user_id VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	id VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_hidden_request_user UNIQUE (request_id, user_id), 
	FOREIGN KEY(request_id) REFERENCES ride_requests (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id)
)



CREATE TABLE ride_events (
	request_id VARCHAR(32) NOT NULL, 
	actor_id VARCHAR(32), 
	event VARCHAR(60) NOT NULL, 
	data TEXT, 
	created_at DATETIME NOT NULL, 
	id VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(request_id) REFERENCES ride_requests (id) ON DELETE CASCADE
)



CREATE TABLE ride_members (
	request_id VARCHAR(32) NOT NULL, 
	user_id VARCHAR(32) NOT NULL, 
	role VARCHAR(10) NOT NULL, 
	status VARCHAR(12) NOT NULL, 
	seats INTEGER NOT NULL, 
	pickup_lat FLOAT NOT NULL, 
	pickup_lng FLOAT NOT NULL, 
	pickup_address TEXT NOT NULL, 
	drop_lat FLOAT NOT NULL, 
	drop_lng FLOAT NOT NULL, 
	drop_address TEXT NOT NULL, 
	matching_code_hash VARCHAR(64), 
	matching_code_plain VARCHAR(12), 
	pickup_order INTEGER, 
	drop_order INTEGER, 
	pickup_eta_min FLOAT, 
	distance_km FLOAT, 
	fare_share_inr FLOAT, 
	detour_km FLOAT NOT NULL, 
	match_score FLOAT NOT NULL, 
	joined_at DATETIME NOT NULL, 
	picked_up_at DATETIME, 
	dropped_at DATETIME, 
	left_at DATETIME, 
	id VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_member_request_user UNIQUE (request_id, user_id), 
	FOREIGN KEY(request_id) REFERENCES ride_requests (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id)
)



CREATE TABLE vehicles (
	driver_id VARCHAR(32) NOT NULL, 
	vehicle_type VARCHAR(20) NOT NULL, 
	registration_number VARCHAR(20) NOT NULL, 
	make_model VARCHAR(120), 
	color VARCHAR(40), 
	seat_capacity INTEGER NOT NULL, 
	is_verified BOOLEAN NOT NULL, 
	id VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (driver_id), 
	FOREIGN KEY(driver_id) REFERENCES driver_profiles (id) ON DELETE CASCADE, 
	UNIQUE (registration_number)
)



CREATE TABLE rides (
	request_id VARCHAR(32) NOT NULL, 
	driver_user_id VARCHAR(32) NOT NULL, 
	offer_id VARCHAR(32), 
	status VARCHAR(20) NOT NULL, 
	vehicle_type VARCHAR(20) NOT NULL, 
	vehicle_registration VARCHAR(20), 
	driver_eta_min FLOAT, 
	otp_verified_at DATETIME, 
	started_at DATETIME, 
	completed_at DATETIME, 
	cancelled_at DATETIME, 
	cancel_reason VARCHAR(200), 
	total_distance_km FLOAT, 
	total_fare_inr FLOAT, 
	platform_fee_inr FLOAT, 
	driver_payout_inr FLOAT, 
	id VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(request_id) REFERENCES ride_requests (id), 
	FOREIGN KEY(driver_user_id) REFERENCES users (id), 
	FOREIGN KEY(offer_id) REFERENCES driver_offers (id)
)



CREATE TABLE payments (
	ride_id VARCHAR(32) NOT NULL, 
	payer_id VARCHAR(32) NOT NULL, 
	amount_inr FLOAT NOT NULL, 
	method VARCHAR(10) NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	reference VARCHAR(120), 
	paid_at DATETIME, 
	id VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_payment_ride_payer UNIQUE (ride_id, payer_id), 
	FOREIGN KEY(ride_id) REFERENCES rides (id), 
	FOREIGN KEY(payer_id) REFERENCES users (id)
)



CREATE TABLE ratings (
	ride_id VARCHAR(32) NOT NULL, 
	rater_id VARCHAR(32) NOT NULL, 
	ratee_id VARCHAR(32) NOT NULL, 
	stars INTEGER NOT NULL, 
	comment VARCHAR(300), 
	created_at DATETIME NOT NULL, 
	id VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_rating_once UNIQUE (ride_id, rater_id, ratee_id), 
	FOREIGN KEY(ride_id) REFERENCES rides (id), 
	FOREIGN KEY(rater_id) REFERENCES users (id), 
	FOREIGN KEY(ratee_id) REFERENCES users (id)
)


