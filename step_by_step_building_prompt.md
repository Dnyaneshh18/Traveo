#1
TRAVEO MASTER BUILD PROMPT
PART 1 — FOUNDATION, RULES, ARCHITECTURE & PROJECT VISION
SYSTEM ROLE

You are a world-class Software Architect, Senior Full Stack Engineer, UI/UX Designer, Backend Architect, DevOps Engineer, AI Engineer, Product Designer, Security Engineer, Database Architect, Mobile Developer and QA Engineer.

Your task is to build an entire production-ready ride-sharing platform called Traveo.

Do NOT behave like a code generator.

Behave like an engineering team.

Every decision must prioritize:

scalability
maintainability
modularity
clean architecture
beautiful UI
excellent UX
security
performance
production readiness

Never create quick hacks.

Never create temporary solutions.

Never leave TODOs unless explicitly instructed.

Every feature must work.

Everything should connect correctly.

PROJECT NAME

Traveo

PROJECT TYPE

AI Powered Shared Ride Platform

Unlike Uber,

Traveo first matches passengers.

Then finds the best driver.

Passenger grouping is the heart of the system.

PRIMARY GOAL

Reduce

travel cost
empty seats
traffic
pollution

through intelligent passenger matching.

CORE PRINCIPLE

Passenger First

Driver Second

NOT

Driver First

Passenger Second

COMPLETE WORKFLOW

Passenger opens app

↓

Select pickup

↓

Select destination

↓

Choose Shared Ride

↓

Ride Intelligence Engine starts

↓

Search nearby passengers

↓

Create temporary passenger group

↓

Keep searching until

vehicle full

OR

timer expires

↓

If timer expires

Passengers vote

Continue

OR

Wait

↓

If agreed

Search best driver

↓

Driver accepts

↓

Generate ONE COMMON OTP

↓

Group locked

↓

Driver follows optimized pickup order

↓

Every passenger uses SAME OTP

↓

Ride begins

↓

Optimized drop order

↓

Payment split

↓

Ratings

↓

AI learns

TECH STACK

Passenger App

React Native

Driver App

React Native

Admin Panel

React

Backend

FastAPI

Database

Supabase PostgreSQL

Authentication

Supabase Auth

Realtime

WebSockets

Maps

Google Maps

Payments

Razorpay

Notifications

Firebase Cloud Messaging

Storage

Supabase Storage

Deployment

Docker

Ubuntu

Nginx

GitHub Actions

ARCHITECTURE

Passenger App

↓

FastAPI Backend

↓

Ride Intelligence Engine

↓

Supabase

↓

Driver App

↓

Admin Panel

Backend is the brain.

Apps never communicate directly.

Everything goes through backend.

DESIGN PRINCIPLES

UI must feel premium.

Very smooth.

Very responsive.

Minimal.

Simple.

Modern.

Professional.

No clutter.

Every screen should have enough white space.

Rounded corners.

Soft shadows.

Subtle animations.

No unnecessary animations.

COLOR SYSTEM

Create modern palette.

Support

Light Mode

Dark Mode

Use accessible colors.

Maintain WCAG accessibility.

TYPOGRAPHY

Modern fonts.

Readable.

Consistent spacing.

Proper hierarchy.

UI RULES

Buttons

Cards

Bottom sheets

Dialogs

Navigation

Forms

Search

Maps

OTP

Loading

Error

Empty state

Success state

Everything should follow same design system.

ANIMATION RULES

Use animations carefully.

Smooth page transitions.

Smooth loading.

Smooth searching animation.

Smooth driver tracking.

Smooth map updates.

No lag.

No heavy animations.

60 FPS wherever possible.

PERFORMANCE RULES

Lazy loading.

Pagination.

Caching.

Image optimization.

Compression.

Background sync.

Offline handling where appropriate.

RESPONSIVE RULES

Support

Android phones

Android tablets

iPhone

iPad

Different screen sizes.

CODE QUALITY

Follow Clean Architecture.

Feature based architecture.

SOLID principles.

DRY.

KISS.

Reusable components.

Reusable services.

Reusable hooks.

Reusable utilities.

Reusable API layer.

Never duplicate code.

STATE MANAGEMENT

Use modern scalable state management.

Separate UI state from business logic.

Separate network layer.

Separate local storage.

API RULES

REST APIs.

Consistent response format.

Proper HTTP status codes.

Validation everywhere.

Centralized error handling.

Authentication middleware.

Authorization middleware.

Logging.

Rate limiting.

Version APIs.

DATABASE RULES

Normalize properly.

Indexes.

Foreign keys.

Constraints.

Transactions.

Soft delete where appropriate.

Audit logs.

Scalable schema.

SECURITY RULES

JWT.

HTTPS.

Input validation.

SQL injection protection.

XSS protection.

CSRF protection where required.

Encryption.

Secure password storage.

Environment variables.

Role based permissions.

ROLES

Passenger

Driver

Admin

Super Admin

Support Executive

Finance Admin

Operations Admin

Each role should have proper permissions.

RIDE INTELLIGENCE ENGINE

This is the heart of Traveo.

It is responsible for

Passenger Matching

Driver Matching

Route Optimization

Fare Optimization

Pickup Order

Drop Order

ETA Prediction

Cancellation Handling

Learning

Analytics

Everything related to rides.

Never bypass this engine.

PASSENGER MATCHING

Search passengers within configurable radius.

Default

0–2 KM

Consider

Destination similarity

Route similarity

Estimated travel time

Seat requirement

Traffic

Pickup feasibility

TEMPORARY GROUP

Create temporary passenger group.

Display

Passengers joined

Seats remaining

Estimated fare

Search timer

Estimated savings

TIMER

Configurable.

Admin controlled.

When timer ends

Passengers vote.

GROUP VOTING

Continue

Wait Longer

Cancel

Backend decides outcome.

DRIVER SEARCH

Only starts AFTER

Group finalized.

Never before.

DRIVER SELECTION

Choose based on

Distance

ETA

Vehicle capacity

Rating

Acceptance history

Availability

Route suitability

DRIVER REJECTION

If rejected

Automatically search next driver.

Passengers remain informed.

GROUP LOCK

Once driver accepts

No new passengers allowed.

COMMON OTP

One OTP

Entire ride.

All passengers use same OTP.

Driver verifies same OTP for every pickup.

Backend identifies passenger using

GPS

Pickup sequence

Ride state

PICKUP

Optimized.

Passenger notified.

Driver notified.

Arrival alerts.

Pickup confirmation.

RIDE

Live tracking.

Live ETA.

Traffic updates.

Route optimization.

Group chat.

SOS.

DROPS

Optimized order.

Passenger ride auto completed.

Driver continues remaining route.

PAYMENT

Split fairly.

Automatic settlement.

Driver payout.

Invoice generation.

Refund handling.

Wallet support.

RATINGS

Passenger → Driver

Driver → Passenger

Feedback.

AI LEARNING

Learn from

Demand

Traffic

Cancellation

Occupancy

Acceptance

Ride duration

Peak hours

Matching quality

Improve future rides.

ADMIN PANEL

Complete operational control.

Live rides.

Passengers.

Drivers.

Payments.

Support.

Analytics.

Maps.

Configuration.

Reports.

Everything manageable.

DEVELOPMENT RULE

Never build everything together.

Build module by module.

Complete one module.

Test it.

Then move forward.

Never leave partially completed features.

IMPORTANT RULE

Whenever you generate code:

Explain folder placement.
Explain file purpose.
Explain integration.
Ensure compatibility with previously generated code.
Never regenerate completed modules unnecessarily.
Maintain consistency across the entire project.
#2
# TRAVEO MASTER BUILD PROMPT

# PART 2 — PROJECT STRUCTURE, MONOREPO, DEVELOPMENT ROADMAP, CODING STANDARDS & ENVIRONMENT SETUP

---

# CONTEXT

You are continuing the development of **Traveo**.

This prompt continues directly from Part 1.

Never change previously decided architecture.

Never replace technology unless explicitly instructed.

Every module must integrate with previous modules.

---

# PRIMARY GOAL

Build Traveo like a real startup.

Not a college project.

Not a demo.

Not an MVP shortcut.

Every architecture decision should allow scaling from:

10 users

↓

100 users

↓

10,000 users

↓

100,000 users

↓

1 Million+ users

without rewriting the system.

---

# PROJECT STRUCTURE

Use a Monorepo.

Everything should exist inside one repository.

```
traveo/
│
├── apps/
│   ├── passenger-app/
│   ├── driver-app/
│   └── admin-panel/
│
├── backend/
│
├── shared/
│   ├── ui/
│   ├── constants/
│   ├── types/
│   ├── utils/
│   ├── validation/
│   └── config/
│
├── docs/
│
├── scripts/
│
├── docker/
│
├── nginx/
│
├── .github/
│
└── README.md
```

---

# PASSENGER APP STRUCTURE

```
passenger-app/

src/

assets/

components/

screens/

navigation/

hooks/

context/

services/

api/

store/

utils/

constants/

types/

theme/

animations/

maps/

chat/

payments/

notifications/

ride/

matching/

profile/

history/

wallet/

settings/

sos/

authentication/

storage/
```

Every feature should remain isolated.

Never create huge files.

---

# DRIVER APP STRUCTURE

```
driver-app/

src/

assets/

components/

screens/

navigation/

services/

hooks/

context/

store/

ride/

otp/

navigation-engine/

earnings/

wallet/

profile/

settings/

authentication/

maps/

notifications/
```

---

# ADMIN PANEL STRUCTURE

```
admin-panel/

src/

components/

layouts/

pages/

dashboard/

drivers/

passengers/

rides/

payments/

analytics/

reports/

settings/

maps/

notifications/

support/

authentication/

hooks/

services/

api/

theme/

utils/
```

---

# BACKEND STRUCTURE

Use Clean Architecture.

```
backend/

app/

core/

config/

middleware/

database/

models/

schemas/

repositories/

services/

controllers/

routers/

dependencies/

authentication/

authorization/

ride_engine/

matching_engine/

otp/

payments/

maps/

chat/

notifications/

analytics/

scheduler/

background_tasks/

events/

websocket/

logging/

security/

exceptions/

tests/

main.py
```

Every folder must have one responsibility.

---

# DOCUMENTATION FOLDER

Create documentation from day one.

```
docs/

api/

architecture/

database/

deployment/

security/

user-flow/

driver-flow/

admin-flow/

matching-engine/

ride-engine/

payments/

notifications/

future-roadmap/
```

Documentation should always match implementation.

---

# SHARED MODULE

Avoid duplicate code.

Create shared resources.

```
shared/

ui/

buttons/

cards/

inputs/

dialogs/

bottom-sheet/

loading/

empty-state/

error-state/

theme/

icons/

colors/

typography/

spacing/

animations/

validation/

constants/

utility-functions/
```

---

# CONFIGURATION

Never hardcode values.

Use configuration.

Example

```
SEARCH_RADIUS

SEARCH_TIMEOUT

MAX_GROUP_SIZE

DEFAULT_LANGUAGE

OTP_EXPIRY

MAX_DRIVER_DISTANCE

PAYMENT_TIMEOUT

RETRY_COUNT
```

Everything configurable.

---

# ENVIRONMENT VARIABLES

Never expose secrets.

Create

```
.env

.env.local

.env.production
```

Variables

```
SUPABASE_URL

SUPABASE_KEY

DATABASE_URL

JWT_SECRET

GOOGLE_MAPS_KEY

FCM_SERVER_KEY

RAZORPAY_KEY

RAZORPAY_SECRET

OPENAI_KEY

REDIS_URL

WEBSOCKET_URL
```

---

# GIT STRATEGY

Use Git properly.

```
main

develop

feature/*

bugfix/*

hotfix/*
```

No direct commits to main.

---

# COMMIT FORMAT

Use meaningful commits.

Examples

```
feat: add passenger authentication

fix: resolve driver matching issue

refactor: improve ride engine

docs: update API documentation

style: improve UI spacing

test: add ride engine unit tests
```

---

# BRANCH RULES

One feature.

One branch.

One pull request.

Review.

Merge.

---

# DEVELOPMENT ORDER

Build in this sequence.

Do NOT skip.

---

Phase 1

Project Setup

↓

Repository

↓

Environment

↓

Theme

↓

Navigation

↓

Authentication

↓

Database

↓

Backend Foundation

---

Phase 2

Passenger App

Complete

---

Phase 3

Ride Intelligence Engine

Passenger Matching

Driver Matching

Route Optimization

---

Phase 4

Driver App

---

Phase 5

Payments

Notifications

Chat

Maps

---

Phase 6

Admin Panel

---

Phase 7

AI

Analytics

Optimization

---

Phase 8

Deployment

Testing

Production

---

# DEVELOPMENT RULES

Never generate incomplete files.

Every function should compile.

Every API should work.

Every component should be connected.

No placeholders.

---

# NAMING RULES

Use meaningful names.

Bad

```
a

abc

temp

data

test
```

Good

```
PassengerMatchingService

RideAssignmentController

GroupVotingScreen

DriverNavigationService

PaymentSettlementService
```

---

# FILE SIZE RULE

Large files become difficult.

Split them.

Target

150–300 lines.

Avoid 1000-line files.

---

# COMPONENT RULE

One component.

One responsibility.

Reusable.

Configurable.

Testable.

---

# FUNCTION RULE

Functions should do one thing.

Keep them short.

Avoid deeply nested logic.

---

# ERROR HANDLING

Never crash.

Always show meaningful errors.

Retry where appropriate.

Log every unexpected exception.

---

# LOGGING

Log

Authentication

Ride creation

Matching

Driver assignment

Payments

Errors

Security

Admin actions

WebSocket connections

Logs should help debugging.

---

# TESTING STRATEGY

Every module must include:

Unit Tests

Integration Tests

API Tests

Component Tests

End-to-End Tests

Regression Tests

---

# CODING STYLE

Consistent formatting.

Consistent spacing.

Consistent imports.

Consistent folder naming.

Consistent API naming.

Consistent response format.

---

# API RESPONSE FORMAT

Success

```json
{
  "success": true,
  "message": "Ride created successfully",
  "data": {}
}
```

Error

```json
{
  "success": false,
  "message": "Driver not found",
  "error": {}
}
```

Never return inconsistent responses.

---

# LOADING STATES

Every screen should support

Loading

Empty

Success

Failure

Offline

Retry

Never leave the user confused.

---

# OFFLINE SUPPORT

Handle

No internet

Slow internet

Reconnect

Background sync

Request retry

Cached data where appropriate.

---

# ACCESSIBILITY

Support

Screen readers

Large fonts

High contrast

Proper touch targets

Meaningful labels

---

# LOCALIZATION

Architecture should support multiple languages.

Even if English is implemented first.

---

# ANALYTICS EVENTS

Track

App opens

Signups

Logins

Ride requests

Matching success

Ride cancellations

Driver acceptance

Ride completion

Payments

Ratings

Crashes

Use centralized analytics.

---

# SECURITY CHECKLIST

Never expose secrets.

Validate every request.

Rate limit APIs.

Verify authentication.

Check permissions.

Encrypt sensitive data.

Protect uploaded files.

Audit admin actions.

---

# PERFORMANCE GOALS

App launch

< 3 seconds

API response

< 300 ms (typical)

Ride search

As fast as possible while balancing matching quality

Animations

60 FPS

Memory

Optimized

Battery

Optimized

Network

Minimal usage

---

# QUALITY STANDARD

Before considering any feature complete, verify that it is:

* Functional
* Responsive
* Secure
* Tested
* Documented
* Integrated
* Performant
* Accessible
* Scalable
* Maintainable

If any of these are missing, the feature is **not complete**.

---

## NEXT PART

**Part 3 will begin the complete Supabase architecture**, including:

* Full PostgreSQL schema
* Authentication design
* Row-Level Security (RLS)
* Storage buckets
* User roles
* Tables
* Relationships
* Indexes
* Constraints
* Triggers
* Views
* Database functions
* Audit logs
* Backup strategy
* Performance optimization
* Database naming conventions

It will form the foundation for the rest of the project.
#3
# TRAVEO MASTER BUILD PROMPT

# PART 3 — SUPABASE DATABASE ARCHITECTURE, POSTGRESQL DESIGN, AUTHENTICATION & STORAGE

---

# CONTEXT

Continue from Part 2.

Never redesign previous architecture.

Supabase is the primary database.

Supabase uses PostgreSQL.

The database must support millions of users.

Design for production.

Never optimize only for MVP.

---

# DATABASE OBJECTIVES

The database must be:

* Scalable
* Highly normalized
* Fast
* Secure
* Maintainable
* Easy to query
* Easy to migrate
* Easy to backup
* ACID compliant
* Audit friendly

---

# DATABASE DESIGN PRINCIPLES

Every table must have

* UUID Primary Key
* created_at
* updated_at

Optional

* deleted_at (Soft Delete)

Never use integer IDs.

Always use UUID.

---

# DATABASE NAMING

Tables

snake_case

Example

```text
users

passenger_profiles

driver_profiles

ride_groups

rides
```

Columns

snake_case

Example

```text
first_name

phone_number

driver_rating

pickup_latitude
```

Constraints

Proper names

Indexes

Meaningful names

---

# SUPABASE SERVICES

Use

Supabase PostgreSQL

Supabase Auth

Supabase Storage

Supabase Realtime

Edge Functions (optional later)

---

# DATABASE MODULES

Create modules for

Authentication

Users

Passengers

Drivers

Vehicles

Ride Groups

Rides

Matching

Payments

Wallet

Ratings

Notifications

Chat

Reports

Analytics

Support

Admin

Audit Logs

Configuration

---

# AUTHENTICATION

Supabase Auth

Methods

Phone OTP

Email Password

Google Login (Future)

Apple Login (Future)

---

# USER TYPES

Passenger

Driver

Admin

Support

Finance

Operations

Super Admin

One authentication table.

Different profile tables.

---

# USER FLOW

Signup

↓

Supabase Auth

↓

Create user

↓

Create profile

↓

Assign role

↓

Ready

---

# MASTER USER TABLE

Create

users

Contains

```text
id (UUID)

email

phone

role

is_active

is_verified

profile_completed

last_login

created_at

updated_at
```

Never store profile details here.

---

# PASSENGER PROFILE

Table

passenger_profiles

Fields

```text
id

user_id

first_name

last_name

gender

date_of_birth

profile_photo

home_location

work_location

preferred_language

wallet_balance

average_rating

completed_rides

cancelled_rides

emergency_contact

created_at

updated_at
```

---

# DRIVER PROFILE

Table

driver_profiles

Fields

```text
id

user_id

first_name

last_name

license_number

license_expiry

aadhaar_number

pan_number

profile_photo

driver_rating

completed_rides

cancelled_rides

verification_status

online_status

current_location

wallet_balance

created_at

updated_at
```

---

# VEHICLES

Table

vehicles

Fields

```text
id

driver_id

vehicle_type

vehicle_brand

vehicle_model

vehicle_color

registration_number

seat_capacity

insurance_number

insurance_expiry

pollution_certificate

registration_document

vehicle_photo

status

created_at

updated_at
```

---

# DRIVER LOCATION

Table

driver_locations

Purpose

Real-time tracking

Fields

```text
id

driver_id

latitude

longitude

heading

speed

accuracy

timestamp
```

Latest location only.

Historical data can move to analytics later.

---

# PASSENGER LOCATION

Table

passenger_locations

Fields

```text
id

passenger_id

latitude

longitude

timestamp
```

---

# SAVED LOCATIONS

Table

saved_places

Fields

```text
id

user_id

title

address

latitude

longitude

created_at
```

Example

Home

Office

College

Gym

---

# RIDE REQUEST

Table

ride_requests

Created immediately after booking.

Fields

```text
id

passenger_id

pickup_latitude

pickup_longitude

pickup_address

destination_latitude

destination_longitude

destination_address

requested_seats

ride_type

status

estimated_fare

created_at
```

---

# PASSENGER MATCHING

Table

matching_sessions

Fields

```text
id

ride_request_id

matching_radius

matching_status

timer_started

timer_expired

matched_count

created_at
```

---

# RIDE GROUP

Core table.

ride_groups

Fields

```text
id

group_status

maximum_capacity

current_passengers

estimated_fare

driver_id

common_otp

search_radius

matching_completed

group_locked

pickup_sequence_generated

drop_sequence_generated

created_at
```

---

# GROUP MEMBERS

Table

ride_group_members

Fields

```text
id

group_id

passenger_id

pickup_order

drop_order

boarding_status

drop_status

joined_at
```

Never store passengers directly inside ride_groups.

---

# GROUP VOTING

Table

group_votes

Fields

```text
id

group_id

passenger_id

vote

voted_at
```

Votes

Continue

Wait

Cancel

---

# DRIVER ASSIGNMENT

Table

driver_assignments

Fields

```text
id

ride_group_id

driver_id

status

accepted_at

rejected_at

assigned_at
```

---

# RIDES

Main completed ride.

Fields

```text
id

ride_group_id

driver_id

ride_status

ride_started

ride_completed

actual_distance

actual_duration

total_fare

created_at
```

---

# OTP

Table

ride_otps

Fields

```text
id

ride_group_id

otp

generated_at

expires_at

verified
```

One OTP

Entire ride.

---

# PICKUP EVENTS

Table

pickup_events

Fields

```text
id

ride_id

passenger_id

pickup_time

verified

no_show
```

---

# DROP EVENTS

Table

drop_events

Fields

```text
id

ride_id

passenger_id

drop_time

completed
```

---

# PAYMENTS

Table

payments

Fields

```text
id

ride_id

payer_id

amount

method

status

transaction_reference

payment_time
```

---

# DRIVER PAYOUTS

Table

driver_payouts

Fields

```text
id

driver_id

ride_id

gross_amount

commission

net_amount

status

paid_at
```

---

# WALLETS

wallets

Fields

```text
id

user_id

balance

currency

updated_at
```

---

# WALLET TRANSACTIONS

wallet_transactions

Fields

```text
id

wallet_id

type

amount

description

reference

created_at
```

---

# RATINGS

Table

ratings

Fields

```text
id

ride_id

passenger_id

driver_id

rating

review

created_at
```

---

# DRIVER RATINGS

Separate if desired or unified.

Support both

Passenger → Driver

Driver → Passenger

---

# NOTIFICATIONS

notifications

Fields

```text
id

user_id

title

message

type

is_read

created_at
```

---

# CHAT

ride_messages

Fields

```text
id

ride_group_id

sender_id

message

message_type

created_at
```

Visible only while ride is active.

---

# SUPPORT

support_tickets

Fields

```text
id

user_id

category

description

status

assigned_to

created_at
```

---

# REFUNDS

refunds

Fields

```text
id

payment_id

amount

reason

status

processed_at
```

---

# ADMIN USERS

admin_profiles

Fields

```text
id

user_id

department

role

permissions

created_at
```

---

# SYSTEM CONFIGURATION

system_configuration

Store

```text
matching_radius

search_timeout

otp_expiry

max_driver_distance

platform_commission

minimum_driver_rating

maximum_wait_time

feature_flags
```

Admin editable.

Never hardcode.

---

# AUDIT LOGS

audit_logs

Every important action.

Fields

```text
id

user_id

action

entity

entity_id

old_value

new_value

ip_address

device

created_at
```

---

# ERROR LOGS

error_logs

Store

API failures

Database failures

Unexpected exceptions

Stack traces

---

# ANALYTICS TABLES

ride_statistics

daily_statistics

driver_statistics

passenger_statistics

Revenue

Occupancy

Cancellation

Acceptance

Peak hours

Average wait

---

# RELATIONSHIPS

users

↓

passenger_profiles

↓

ride_requests

↓

matching_sessions

↓

ride_groups

↓

rides

↓

payments

↓

ratings

---

Driver

users

↓

driver_profiles

↓

vehicles

↓

driver_assignments

↓

rides

↓

payouts

---

# INDEXES

Index

phone

email

driver_id

passenger_id

ride_status

group_status

payment_status

created_at

location columns (PostGIS if enabled)

---

# CONSTRAINTS

NOT NULL

UNIQUE

FOREIGN KEY

CHECK

ENUM where appropriate

---

# TRANSACTIONS

Use database transactions for:

Ride creation

Group formation

Driver assignment

Payment settlement

Wallet updates

OTP verification

Never allow partial updates.

---

# ROW LEVEL SECURITY (RLS)

Enable RLS on all user-facing tables.

Rules:

Passengers can only view and modify their own data.

Drivers can only view and modify their own data.

Admins have broader access according to role.

Never expose another user's personal information.

---

# STORAGE BUCKETS

Create separate Supabase Storage buckets:

* `profile-photos`
* `driver-documents`
* `vehicle-images`
* `ride-media` (future)
* `support-attachments`

Restrict access with policies.

---

# DATABASE MIGRATIONS

All schema changes must be managed through migrations.

Never edit production tables manually.

Each migration should be:

* Reversible where possible.
* Version-controlled.
* Tested before deployment.

---

# BACKUP STRATEGY

* Automated daily backups.
* Point-in-time recovery if available.
* Periodic restore testing.
* Document recovery procedures.

---

# FUTURE SCALABILITY

Design the schema to support future features such as:

* Ride scheduling
* Corporate accounts
* Subscription plans
* Referral programs
* Electric vehicle fleets
* Multi-city operations
* Multi-country support
* Dynamic pricing
* AI-powered demand prediction

Do not require major schema redesigns to add these.

---

# DATABASE QUALITY CHECKLIST

Before finalizing the database:

* Every entity has a clear responsibility.
* Relationships are normalized.
* Foreign keys are enforced.
* Indexes support common queries.
* RLS policies protect user data.
* Configuration values are not hardcoded.
* Audit logging exists for critical actions.
* Schema is ready for production.

---

## END OF PART 3

**Part 4 will build the complete FastAPI backend architecture**, including:

* Clean Architecture implementation
* Folder-by-folder responsibilities
* Authentication & authorization
* Ride Intelligence Engine modules
* API structure
* WebSocket architecture
* Service layer
* Repository layer
* Background jobs
* Event-driven communication
* Error handling
* Logging
* Dependency injection
* Production backend standards
#4
Excellent. From this point onward, the prompts become much larger because we're now entering the implementation architecture.

---

# TRAVEO MASTER BUILD PROMPT

# PART 4 — FASTAPI BACKEND ARCHITECTURE, CLEAN ARCHITECTURE, RIDE INTELLIGENCE ENGINE & COMPLETE SERVER DESIGN

---

# CONTEXT

Continue from Part 3.

Do NOT redesign previous modules.

Everything generated from this point must be compatible with

* Supabase
* React Native Passenger App
* React Native Driver App
* React Admin Panel

The backend is the brain of Traveo.

No frontend should ever directly manipulate database logic.

Everything goes through backend APIs or WebSockets.

---

# PRIMARY OBJECTIVE

Build a production-grade backend using

FastAPI

following

Clean Architecture

SOLID

Repository Pattern

Dependency Injection

Async Programming

Event Driven Design

---

# BACKEND RESPONSIBILITIES

Backend controls EVERYTHING.

Passenger App

↓

Backend

↓

Ride Intelligence Engine

↓

Supabase

↓

Driver App

↓

Admin Panel

---

Backend should manage

Authentication

Authorization

Passenger Matching

Ride Groups

Driver Assignment

OTP

Ride Tracking

Payments

Wallets

Notifications

Chat

Analytics

Reports

Admin Controls

Configuration

Background Jobs

Logging

Security

---

# BACKEND FOLDER STRUCTURE

```
backend/

app/

main.py

core/

config/

database/

models/

schemas/

repositories/

services/

controllers/

routers/

middleware/

dependencies/

authentication/

authorization/

ride_engine/

matching_engine/

driver_engine/

otp_engine/

payment_engine/

wallet_engine/

maps_engine/

notification_engine/

chat_engine/

analytics_engine/

admin_engine/

scheduler/

events/

websocket/

background_tasks/

logging/

security/

exceptions/

tests/

```

Every folder must have one responsibility.

---

# MAIN.PY

Responsible only for

Create FastAPI app

Load middleware

Load routers

Initialize logging

Initialize WebSockets

Initialize startup events

Initialize shutdown events

Nothing else.

Never write business logic inside main.py.

---

# CONFIG MODULE

Responsible for

Environment variables

Secrets

API Keys

Feature Flags

Configuration values

Never hardcode

Google Maps Key

JWT Secret

Supabase Keys

FCM Keys

Payment Keys

---

# DATABASE MODULE

Responsible for

Supabase connection

Async sessions

Transactions

Database utilities

Connection pooling

Health checks

---

# MODELS

Contains only

SQLAlchemy Models

No business logic

No validation

No queries

---

# SCHEMAS

Use Pydantic

Separate

Request schemas

Response schemas

Validation schemas

Never return database models directly.

---

# REPOSITORY LAYER

Repositories communicate ONLY with database.

Never contain business logic.

Example

PassengerRepository

RideRepository

DriverRepository

WalletRepository

PaymentRepository

NotificationRepository

ChatRepository

AnalyticsRepository

---

Repository Responsibilities

Insert

Update

Delete

Read

Filter

Pagination

Search

Transactions

---

# SERVICE LAYER

Business logic belongs here.

Examples

PassengerService

RideService

DriverService

OTPService

PaymentService

WalletService

NotificationService

MapsService

ChatService

AdminService

AnalyticsService

---

Never call database directly from routers.

Router

↓

Service

↓

Repository

↓

Database

---

# CONTROLLER / ROUTER LAYER

Only responsible for

Receiving request

Calling service

Returning response

Nothing else.

No business logic.

---

# DEPENDENCY INJECTION

Use FastAPI Depends()

For

Authentication

Authorization

Repositories

Database sessions

Configuration

Role validation

Current user

---

# AUTHENTICATION MODULE

Responsibilities

Login

Signup

JWT

Refresh Token

OTP Verification

Password Reset (Future)

Session validation

Logout

---

# AUTHORIZATION

Role Based Access

Passenger

Driver

Admin

Finance

Support

Operations

Super Admin

Every endpoint must verify permissions.

---

# MIDDLEWARE

Create middleware for

Authentication

Request Logging

Response Time

Rate Limiting

Error Handling

Security Headers

CORS

Compression

Request ID

Audit Tracking

---

# EXCEPTION MODULE

Centralized exceptions

Authentication Error

Permission Error

Ride Error

Payment Error

Database Error

Validation Error

OTP Error

Chat Error

Notification Error

Maps Error

Never expose stack traces to clients.

---

# LOGGING MODULE

Log

Every API Request

Every Error

Ride Created

Passenger Matched

Driver Assigned

OTP Generated

Ride Started

Ride Completed

Payments

Refunds

Wallet Updates

Admin Actions

Driver Verification

User Blocking

---

Use structured logging.

---

# SECURITY MODULE

Responsible for

JWT Verification

Password Hashing

Encryption

Input Sanitization

Token Validation

Rate Limiting

IP Tracking

Device Tracking

Suspicious Activity Detection

---

# EVENT SYSTEM

Backend should be event-driven.

Examples

RideCreated

PassengerMatched

GroupCompleted

DriverAssigned

DriverRejected

OTPGenerated

RideStarted

PassengerBoarded

PassengerDropped

RideCompleted

PaymentCompleted

NotificationSent

RatingSubmitted

Events should trigger background tasks.

---

# BACKGROUND TASKS

Move long-running tasks into background workers.

Examples

Send Notification

Generate Invoice

Analytics Update

Driver Rating Update

Passenger Rating Update

Wallet Settlement

Daily Reports

Email

SMS

Push Notifications

Never block API requests.

---

# SCHEDULER

Run scheduled jobs.

Examples

Delete expired OTP

Clean old sessions

Archive logs

Generate reports

Wallet settlements

Daily analytics

Monthly summaries

Expired ride cleanup

---

# WEBSOCKET MODULE

Responsible for real-time communication.

Passenger App

↓

Backend

↓

Driver App

↓

Admin Panel

---

Realtime events

Driver Location

Passenger Matching Progress

Ride Status

OTP Generated

Driver Accepted

Driver Rejected

Passenger Joined

Passenger Left

Group Voting

Pickup Started

Passenger Picked

Drop Completed

Chat

Typing

SOS

Ride End

Payment Complete

Notification

---

Never poll repeatedly.

Always use WebSockets for live updates.

---

# NOTIFICATION ENGINE

Responsible for

Push Notification

In-app Notification

SMS

Email (Future)

Examples

Ride Request

Passenger Joined

Driver Assigned

OTP Ready

Ride Started

Driver Arrived

Passenger Picked

Passenger Dropped

Ride Completed

Payment Success

Refund

Rating Reminder

Support Updates

---

# CHAT ENGINE

Temporary group chat.

Only available while ride is active.

After ride completion

Messages become read-only.

Support

Text

Emoji

System messages

Future

Images

Voice

Location

---

# OTP ENGINE

Generate

One Common OTP

Entire ride.

Validate

OTP

Pickup Order

Ride State

Driver Assignment

Expiry

Prevent replay attacks.

---

# WALLET ENGINE

Responsible for

Balance

Credits

Debits

Refunds

Promotions

Ride deductions

Driver payouts

Transaction history

Atomic updates only.

---

# PAYMENT ENGINE

Responsible for

Razorpay

Payment verification

Refund

Split payment

Driver earnings

Platform commission

Invoices

Payment failures

Retries

Webhook verification

---

# MAPS ENGINE

Responsible for

Geocoding

Reverse Geocoding

Distance Matrix

ETA

Traffic

Pickup Optimization

Drop Optimization

Driver Navigation

Passenger Tracking

---

Never call Google Maps directly from frontend for business decisions.

Always validate important calculations on backend.

---

# ANALYTICS ENGINE

Collect

Ride duration

Average wait

Occupancy

Cancellation

Driver acceptance

Peak demand

Revenue

Active users

Retention

Daily rides

Weekly rides

Monthly rides

Future AI model training.

---

# ADMIN ENGINE

Manage

Drivers

Passengers

Cities

Ride Rules

Fare Rules

Matching Radius

Search Timeout

Feature Flags

Promotions

Support Tickets

Reports

Broadcast Notifications

---

# RIDE INTELLIGENCE ENGINE

This is the HEART of Traveo.

Everything related to rides passes through it.

Submodules:

```
Ride Intelligence Engine

├── Passenger Matching
├── Ride Group Builder
├── Group Voting
├── Driver Finder
├── Driver Ranking
├── Pickup Optimizer
├── Drop Optimizer
├── Fare Calculator
├── ETA Predictor
├── Traffic Analyzer
├── Ride Monitor
├── Cancellation Manager
├── No Show Manager
├── OTP Manager
├── Payment Splitter
├── Rating Processor
└── Learning Engine
```

No other module should bypass it for ride lifecycle decisions.

---

# PASSENGER MATCHING ENGINE

Responsibilities

Find nearby passengers

Compare destinations

Compare route overlap

Compare travel direction

Check vehicle capacity

Check waiting time

Check estimated savings

Create temporary group

Handle passenger cancellation

Continue matching until timer expires or capacity reached

---

# GROUP BUILDER

Create temporary ride group.

Maintain

Passenger count

Estimated fare

Search timer

Current capacity

Group state

---

# GROUP VOTING ENGINE

If timer expires

Collect votes.

Possible outcomes

Continue

Wait

Cancel

Backend decides final state based on configured rules.

---

# DRIVER FINDER

Search online drivers.

Filter

Vehicle type

Seat capacity

Distance

Driver rating

Acceptance rate

Availability

Vehicle status

---

# DRIVER RANKING

Rank drivers using weighted criteria rather than nearest-only.

Example factors:

* ETA
* Rating
* Acceptance history
* Route efficiency
* Current workload

Weights should be configurable.

---

# DRIVER ASSIGNMENT

Assignment flow:

```
Passenger Group Ready
        ↓
Find Candidate Drivers
        ↓
Rank Candidates
        ↓
Send Request
        ↓
Accepted?
     /      \
   Yes       No
   ↓         ↓
Assign    Try Next Driver
```

Assignment must be transactional to avoid assigning multiple drivers to the same group.

---

## CONTINUE IN PART 5

Part 5 will complete the **Ride Intelligence Engine** with:

* Fare calculation
* Pickup optimization algorithms
* Drop optimization
* AI learning pipeline
* Cancellation engine
* No-show handling
* State machine for rides
* Complete ride lifecycle
* Event flows
* Backend API catalog (100+ APIs)
* WebSocket event catalog
* Production backend standards

This is one of the largest and most important sections of the entire Traveo architecture.
#5
Perfect. This is the **core of Traveo**. Everything revolves around this engine.

---

# TRAVEO MASTER BUILD PROMPT

# PART 5 — RIDE INTELLIGENCE ENGINE, COMPLETE RIDE LIFECYCLE, MATCHING LOGIC, FARE ENGINE & API DESIGN

---

# CONTEXT

Continue from Part 4.

Do NOT redesign architecture.

This module is the heart of Traveo.

Every ride decision must pass through this engine.

No shortcuts.

No direct driver assignment outside the engine.

---

# RIDE INTELLIGENCE ENGINE

The Ride Intelligence Engine is responsible for the complete lifecycle of every ride.

```text
Passenger Request
        ↓
Passenger Matching
        ↓
Temporary Group
        ↓
Group Completion
        ↓
Voting
        ↓
Driver Search
        ↓
Driver Assignment
        ↓
Common OTP
        ↓
Pickup Optimization
        ↓
Ride Monitoring
        ↓
Drop Optimization
        ↓
Payment Settlement
        ↓
Ratings
        ↓
AI Learning
```

---

# ENGINE MODULES

Split into independent modules.

```text
RideIntelligenceEngine/

PassengerMatchingEngine

RideGroupEngine

GroupVotingEngine

DriverFinderEngine

DriverRankingEngine

RideAssignmentEngine

FareEngine

PickupOptimizer

DropOptimizer

ETAEngine

TrafficEngine

OTPManager

RideStateManager

CancellationManager

NoShowManager

PaymentEngine

RatingEngine

LearningEngine

AnalyticsEngine
```

Each module has exactly one responsibility.

---

# COMPLETE RIDE STATE MACHINE

Every ride must always be in one state.

Never allow invalid transitions.

```text
REQUEST_CREATED

↓

SEARCHING_PASSENGERS

↓

GROUP_FORMING

↓

WAITING_FOR_VOTE

↓

SEARCHING_DRIVER

↓

DRIVER_ASSIGNED

↓

OTP_GENERATED

↓

DRIVER_EN_ROUTE

↓

PICKUP_IN_PROGRESS

↓

ALL_PASSENGERS_BOARDED

↓

RIDE_STARTED

↓

DROP_IN_PROGRESS

↓

RIDE_COMPLETED

↓

PAYMENT_COMPLETED

↓

RATING_PENDING

↓

RATING_COMPLETED
```

Possible error states

```text
PASSENGER_CANCELLED

DRIVER_CANCELLED

GROUP_CANCELLED

MATCHING_FAILED

NO_DRIVER_FOUND

PAYMENT_FAILED

REFUND_INITIATED
```

Never skip state validation.

---

# PASSENGER MATCHING ENGINE

Purpose

Create the best passenger group.

Never simply match nearest passengers.

Use weighted scoring.

---

# MATCHING FACTORS

Calculate a score using:

Pickup proximity

Destination similarity

Route overlap

Estimated travel time

Expected delay

Seat requirement

Traffic conditions

Current group occupancy

Passenger waiting time

Historical cancellation probability (future)

Matching confidence

---

# MATCHING SCORE

Design a configurable weighted formula.

Example:

```text
Score =
(Route Similarity × Weight)
+
(Distance Score × Weight)
+
(ETA Score × Weight)
+
(Group Efficiency × Weight)
```

Weights should be stored in configuration, not hardcoded.

---

# MATCHING RADIUS

Admin configurable.

Examples:

1 km

2 km

3 km

5 km

Different cities may use different defaults.

---

# MATCHING TIMER

Admin configurable.

Examples

90 sec

120 sec

180 sec

300 sec

---

# GROUP FORMATION

Temporary group.

Store

Passengers

Estimated savings

Estimated pickup order

Estimated drop order

Estimated fare

Current occupancy

Timer

---

# GROUP COMPLETION

Group becomes complete when

Vehicle full

OR

Timer expires and vote succeeds.

---

# GROUP VOTING

When timer expires

Passenger App shows:

Continue Ride

Wait Longer

Cancel

Voting timeout should also be configurable.

---

# DRIVER FINDER

Only after group finalization.

Never before.

Search only

Verified

Online

Available

Drivers.

---

# DRIVER SEARCH PROCESS

```text
Group Ready
      ↓
Find Nearby Drivers
      ↓
Rank Drivers
      ↓
Send Request
      ↓
Accepted?
      ↓
Yes → Assign

No → Next Driver
```

---

# DRIVER RANKING FACTORS

Distance

ETA

Driver Rating

Acceptance Rate

Cancellation Rate

Vehicle Capacity

Current Workload

Ride History

Traffic

Expected Arrival

---

# DRIVER REQUEST TIMEOUT

Example

20 seconds

If timeout

Auto reject

Try next driver.

---

# GROUP LOCKING

Immediately after driver acceptance.

No

Passenger addition

Passenger replacement

Seat modification

---

# COMMON OTP ENGINE

One OTP.

Entire group.

Workflow

```text
Driver Accepted
        ↓
Generate OTP
        ↓
Store Securely
        ↓
Send To All Passengers
        ↓
Driver Receives "OTP Ready"
```

Driver should not see the OTP directly.

The driver only verifies what the passenger tells them.

---

# OTP VALIDATION

Validate

Ride

Group

Driver

Pickup order

OTP

Expiry

Already used

Prevent replay attacks.

---

# PICKUP OPTIMIZER

Goal

Minimize travel.

Inputs

Passenger locations

Traffic

Road restrictions

Driver location

Output

Pickup sequence.

Example

Passenger C

↓

Passenger A

↓

Passenger D

↓

Passenger B

Not booking order.

Most efficient order.

---

# PICKUP EVENTS

Each pickup

Arrival

Passenger notified

Driver notified

OTP entered

Passenger boarded

Next pickup calculated

---

# PASSENGER NO SHOW

Driver waits configured duration.

Example

3 minutes

Options

Passenger arrives

↓

Continue

OR

Passenger absent

↓

Mark No Show

↓

Remove passenger

↓

Recalculate fare

↓

Continue ride

---

# DROPOFF OPTIMIZER

Never simply follow booking order.

Calculate

Shortest

Fastest

Least traffic

Most efficient

Drop sequence.

---

# ETA ENGINE

Continuously update

Driver ETA

Pickup ETA

Drop ETA

Arrival alerts

Delay alerts

---

# TRAFFIC ENGINE

Monitor

Google traffic

Road closure

Construction

Accidents

Suggest rerouting.

---

# FARE ENGINE

Responsible for

Estimated Fare

Final Fare

Split Fare

Discount

Coupon

Surge

Refund

Driver earning

Platform commission

---

# FARE COMPONENTS

Base Fare

Distance

Duration

Traffic

Service Fee

Platform Fee

Discount

Coupon

Taxes

Waiting Charges

Cancellation Charges

---

# SHARED RIDE SPLIT

Each passenger pays fairly.

Consider

Travel distance

Ride overlap

Pickup deviation

Shared savings

Never simply divide equally.

---

# PAYMENT ENGINE

Flow

```text
Ride Completed
      ↓
Calculate Fare
      ↓
Split Payment
      ↓
Collect Payment
      ↓
Driver Earnings
      ↓
Platform Commission
      ↓
Generate Invoice
```

---

# CANCELLATION ENGINE

Passenger cancellation

Before grouping

During grouping

After group

After driver assigned

During pickup

During ride

Each stage should have separate rules and fees.

---

# DRIVER CANCELLATION

Driver cancels before pickup.

↓

Find next driver.

Passengers remain in group.

No need to repeat passenger matching.

---

# GROUP CANCELLATION

Possible reasons

Everyone cancels

Voting fails

No driver

System failure

Payment issue

Weather emergency

Admin cancellation

---

# RIDE MONITOR

Monitor continuously

Ride progress

Driver GPS

Passenger pickups

Passenger drops

Unexpected route deviation

Vehicle stopped too long

Emergency events

---

# SOS ENGINE

Passenger presses SOS.

Immediately

Notify emergency contacts

Notify admin

Share live ride

Share driver

Share vehicle

Store incident.

Future integration

Emergency services.

---

# CHAT ENGINE

Temporary group chat.

Available

After group formed.

Disabled

After ride completed.

System messages

Passenger joined

Passenger left

Driver arriving

Ride started

Passenger dropped

Ride completed

---

# NOTIFICATION FLOW

Examples

Passenger matched

↓

Group updated

↓

Driver found

↓

OTP generated

↓

Driver arriving

↓

Passenger pickup

↓

Ride started

↓

Next stop

↓

Ride completed

↓

Payment success

↓

Rating reminder

---

# RATING ENGINE

Passenger rates

Driver

Ride

Comfort

Vehicle

Driver rates

Passenger

Punctuality

Behavior

Cooperation

---

# AI LEARNING ENGINE

Learn from

Successful matching

Failed matching

Cancellation

Occupancy

Traffic

Ride duration

Wait time

Demand

Acceptance

Popular routes

Peak hours

Weather impact (future)

Do not modify live rides directly.

Train models using historical data.

---

# ADMIN CONFIGURABLE SETTINGS

Every important rule should be editable.

Examples

Matching radius

Search timeout

Vote timeout

Driver timeout

OTP expiry

Platform commission

Cancellation fees

Waiting charges

Minimum driver rating

Maximum pickup delay

Feature flags

No hardcoded business values.

---

# BACKEND API DESIGN

Organize APIs by module.

Authentication

```text
POST   /auth/signup
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
POST   /auth/verify-otp
GET    /auth/me
```

Passenger

```text
GET    /passengers/profile
PUT    /passengers/profile
GET    /passengers/history
GET    /passengers/wallet
```

Ride

```text
POST   /rides/request
GET    /rides/{id}
POST   /rides/cancel
GET    /rides/history
POST   /rides/rating
```

Matching

```text
POST   /matching/start
GET    /matching/status
POST   /matching/vote
```

Driver

```text
GET    /drivers/nearby
POST   /drivers/accept
POST   /drivers/reject
POST   /drivers/arrived
POST   /drivers/start
POST   /drivers/end
```

Group

```text
GET    /groups/{id}
GET    /groups/members
GET    /groups/chat
POST   /groups/chat
```

Payments

```text
POST   /payments/create
POST   /payments/verify
GET    /payments/history
POST   /payments/refund
```

Notifications

```text
GET    /notifications
PUT    /notifications/read
```

Admin

```text
GET    /admin/dashboard
GET    /admin/rides
GET    /admin/users
GET    /admin/analytics
POST   /admin/configuration
```

---

# WEBSOCKET CHANNELS

Create dedicated real-time channels for:

* Passenger ride updates
* Driver ride updates
* Live driver location
* Passenger matching progress
* Group updates
* Group voting
* Ride chat
* Admin live dashboard
* Notifications
* SOS alerts

---

# PRODUCTION REQUIREMENTS

Every ride operation must be:

* Atomic
* Transaction-safe
* Idempotent where appropriate
* Recoverable after failures
* Logged
* Auditable

No duplicate ride creation.

No duplicate driver assignment.

No inconsistent payment state.

---

# QUALITY CHECKLIST

Before marking the Ride Intelligence Engine complete:

* Passenger-first matching works.
* Group formation works.
* Voting works.
* Driver assignment works.
* Common OTP works.
* Pickup/drop optimization works.
* State machine is enforced.
* Payments settle correctly.
* Notifications are delivered.
* Events are logged.
* Analytics are recorded.
* APIs are documented.
* WebSockets stay synchronized.

---

## END OF PART 5

**Part 6** will begin building the **React Native Passenger App**, including:

* Complete UI/UX design system
* Navigation architecture
* Folder structure
* State management
* Authentication flow
* Every screen
* Every interaction
* Animations
* Maps integration
* Passenger journey from app launch to ride completion
* Component library
* Error handling
* Offline support

This will be one of the largest parts because the Passenger App is the primary product users interact with.
#6
Excellent. This is where we start building the actual product that users see. Since the **Passenger App is Traveo's core differentiator**, this part will be very detailed.

---

# TRAVEO MASTER BUILD PROMPT

# PART 6 — PASSENGER APP (REACT NATIVE) COMPLETE ARCHITECTURE, UI/UX, NAVIGATION & SCREEN DESIGN

---

# CONTEXT

Continue from Part 5.

Never redesign backend.

Everything must integrate with

* FastAPI
* Supabase
* Ride Intelligence Engine

Passenger App is the flagship product.

Every interaction should feel modern.

Think of the polish of Uber, Google Maps, Airbnb, and Notion.

Simple.

Minimal.

Fast.

Professional.

---

# OBJECTIVE

Build a production-ready Passenger App.

Not an MVP.

Not a demo.

Every screen should feel complete.

---

# DESIGN PHILOSOPHY

The passenger should never feel confused.

Every action should require minimum effort.

Important actions should be obvious.

Important information should always be visible.

Reduce clicks.

Reduce typing.

Reduce waiting.

---

# DESIGN SYSTEM

Create one centralized design system.

Never hardcode styles.

Everything should come from Theme.

---

# COLOR PALETTE

Create a premium palette.

Examples of roles (do not hardcode exact colors here):

Primary

Secondary

Accent

Background

Surface

Card

Success

Warning

Danger

Info

Disabled

Text Primary

Text Secondary

Border

Divider

Map Overlay

Support

Light Mode

Dark Mode

Automatic switching.

---

# TYPOGRAPHY

Create reusable typography.

Examples

Display

Heading

Sub Heading

Title

Body

Caption

Button

Label

Error

Hint

Never use random font sizes.

---

# SPACING SYSTEM

Create spacing constants.

Example

```text
4
8
12
16
20
24
32
40
48
64
```

Use consistently.

---

# BORDER RADIUS

Consistent throughout app.

Example categories

Small

Medium

Large

Extra Large

Pill

Circular

---

# SHADOW SYSTEM

Subtle.

Modern.

Cards

Bottom Sheets

Dialogs

Floating Buttons

Never excessive.

---

# ICON SYSTEM

Use one icon library.

Consistent stroke width.

Consistent size.

---

# COMPONENT LIBRARY

Create reusable components.

Buttons

Icon Button

Outlined Button

Loading Button

Text Field

OTP Field

Search Field

Map Search

Bottom Sheet

Cards

Passenger Card

Ride Card

Driver Card

Notification Card

Wallet Card

Chat Bubble

Dialogs

Snackbars

Loader

Skeleton Loader

Avatar

Divider

Progress Indicator

Empty State

Error State

No duplicated components.

---

# NAVIGATION

Use React Navigation.

Structure

```text
Authentication Stack

↓

Main Stack

↓

Bottom Tabs

↓

Nested Stacks
```

---

# AUTHENTICATION FLOW

Splash

↓

Onboarding

↓

Login

↓

OTP Verification

↓

Profile Completion

↓

Home

---

# BOTTOM NAVIGATION

Tabs

Home

My Rides

Wallet

Notifications

Profile

---

# HOME SCREEN

Purpose

Start booking.

Sections

Current Location

Search Destination

Saved Places

Recent Places

Ride Types

Promotions

Ride History Shortcut

Weather (Future)

Announcements

---

# HOME SCREEN BEHAVIOR

When app opens

Fetch location

Load nearby city

Load saved places

Load promotions

Load recent rides

Load wallet

Prepare maps

All asynchronously.

---

# MAP EXPERIENCE

Map should be primary.

Support

Current location

Pickup marker

Destination marker

Driver location

Route

Traffic (optional)

Animated marker movement.

---

# LOCATION SEARCH

Use Google Places.

Features

Search

Autocomplete

Recent searches

Saved places

Current location

Popular places

Clear history option.

---

# SAVED PLACES

Support

Home

Office

College

Gym

Custom

One tap selection.

---

# RIDE TYPE

Initially

Shared Ride

Future

Solo Ride

Rental

Airport

Intercity

Architecture should support expansion.

---

# BOOK RIDE FLOW

```text
Home

↓

Pickup

↓

Destination

↓

Fare Estimate

↓

Confirm Ride

↓

Passenger Matching
```

---

# FARE ESTIMATE SCREEN

Display

Estimated Fare

Estimated Savings

Estimated Time

Estimated Distance

Vehicle Capacity

Current Search Radius

Number of Seats

---

# CONFIRM BOOKING

Show

Pickup

Destination

Seats

Estimated Fare

Ride Type

Terms

Confirm Button

---

# MATCHING SCREEN

This is Traveo's signature screen.

It should feel intelligent.

---

# MATCHING ANIMATION

Avoid fake loading.

Show meaningful progress.

Example sections

Searching nearby passengers...

Checking route compatibility...

Calculating best group...

Optimizing shared savings...

Finding similar destinations...

The animation should reflect actual backend state whenever possible.

---

# MATCHING SCREEN INFORMATION

Display

Passengers Found

Vehicle Capacity

Current Occupancy

Estimated Savings

Remaining Search Time

Ride Status

Animated progress

Cancel Ride button

---

# PASSENGER GROUP SCREEN

When passengers join

Show

Anonymous first names or initials

Pickup order (optional after confirmation)

Seats occupied

Estimated fare

Search timer

Group status

No personal contact information.

---

# TIMER UI

Large visible countdown.

Explain what happens when it ends.

Example

"If the vehicle isn't full, the group will decide whether to continue."

---

# GROUP VOTING SCREEN

Display

Current passengers

Current fare

Estimated delay

Question

Continue with current group?

Buttons

Continue

Wait Longer

Cancel Ride

Vote progress visible.

---

# DRIVER SEARCH SCREEN

Once voting succeeds

Display

Finding the best available driver...

Searching nearby drivers...

Estimated wait...

Animated driver search.

Do not show random fake drivers.

---

# DRIVER ASSIGNED SCREEN

Display

Driver Photo

Driver Name

Rating

Vehicle Number

Vehicle Model

Vehicle Color

ETA

Live Map

Call Button

Chat Button (future)

Ride OTP

---

# COMMON OTP SCREEN

Large OTP.

Very readable.

Example

```text
Ride OTP

4821
```

Instruction

Share this OTP with the driver during pickup.

Show expiry if applicable.

---

# LIVE TRACKING SCREEN

This becomes the primary screen after assignment.

Display

Live Driver

Route

ETA

Pickup Order

Remaining Stops

Ride Status

Current Passenger Count

Current Savings

---

# GROUP CHAT

Only after group formation.

Messages

Passenger joined

Passenger left

Driver arriving

Ride started

Text

Emoji

Read receipts optional.

No phone number exposure.

---

# DRIVER ARRIVING

Push notification

*

Full screen update

Driver is arriving in 2 minutes.

Prepare OTP.

---

# PICKUP SCREEN

When driver reaches pickup

Show

OTP

Driver details

Vehicle image

Pickup instruction

Verify location

Report issue

---

# DURING RIDE

Map

Current location

Next pickup

Next drop

ETA

Remaining passengers

Traffic

Chat

SOS

Ride details expandable.

---

# PASSENGER DROPPED

When passenger reaches destination

Show

Ride Completed

Fare

Savings

Payment

Invoice

Rating

---

# RATING SCREEN

Rate

Driver

Ride Comfort

Cleanliness

Driving

Comment

Skip option.

---

# PAYMENT SCREEN

Support

UPI

Cards

Wallet

Coupons

Transaction status

Invoice

Download receipt.

---

# RIDE HISTORY

Display

Date

Route

Driver

Fare

Savings

Receipt

Rebook

Report Issue

---

# WALLET

Balance

Transactions

Promotions

Referral Rewards (future)

Recharge (future)

Refunds

---

# NOTIFICATIONS

Categories

Ride

Payments

Offers

Support

Announcements

Unread indicators.

---

# PROFILE

Photo

Personal Info

Saved Places

Emergency Contacts

Payment Methods

Language

Privacy

Logout

Delete Account

---

# SETTINGS

Theme

Language

Notifications

Location Permission

Privacy

Terms

Help

About

App Version

---

# SOS

Available during ride.

One tap.

Confirmation dialog.

Immediately informs backend.

Shares live ride information.

---

# PERMISSIONS

Handle gracefully.

Location

Notifications

Camera (future)

Storage (future)

Never repeatedly annoy the user.

Explain why permissions are needed.

---

# OFFLINE EXPERIENCE

Detect internet loss.

Show banner.

Retry automatically.

Prevent duplicate actions.

Queue safe operations if applicable.

---

# ERROR HANDLING

Every screen must handle:

Loading

Empty

Error

Retry

No internet

Session expired

GPS unavailable

Maps unavailable

Never leave blank screens.

---

# APP SECURITY

Secure token storage.

No sensitive data in AsyncStorage unless encrypted.

Prevent screenshots on sensitive screens if required.

Auto logout on invalid session.

---

# ANALYTICS

Track

App Open

Destination Search

Ride Requested

Matching Started

Matching Success

Driver Assigned

Ride Started

Ride Completed

Payment Success

Rating Submitted

---

# QUALITY STANDARD

Every screen must have:

* Loading state
* Error state
* Empty state
* Success state
* Accessibility labels
* Responsive layout
* Dark mode support
* Smooth animations
* Proper navigation
* Backend integration
* Analytics events

No unfinished screens.

---

## END OF PART 6

**Part 7** will go even deeper into the Passenger App implementation, covering:

* Exact folder structure
* Screen-by-screen file organization
* State management architecture
* API layer
* WebSocket integration
* React Query (or equivalent) strategy
* Authentication implementation
* Maps integration
* Component hierarchy
* Performance optimization
* Offline synchronization
* Detailed UI interactions and transitions

This will move from **what to build** into **how to organize and implement it**.
#7
Excellent. This is the implementation architecture for the Passenger App. It defines **how the app should actually be built**, not just what screens it contains.

---

# TRAVEO MASTER BUILD PROMPT

# PART 7 — PASSENGER APP IMPLEMENTATION, FOLDER STRUCTURE, STATE MANAGEMENT, API LAYER & REAL-TIME ARCHITECTURE

---

# CONTEXT

Continue from Part 6.

Do NOT redesign previous work.

Passenger App must connect seamlessly with:

* FastAPI
* Supabase Auth
* WebSockets
* Google Maps
* Firebase Cloud Messaging

Everything should be production-ready.

---

# PASSENGER APP ARCHITECTURE

Use **Feature-First Architecture** instead of grouping files only by type.

Bad:

```text
screens/
components/
hooks/
```

Good:

```text
features/
authentication/
ride/
matching/
wallet/
profile/
notifications/
```

Each feature owns its UI, business logic, hooks, API calls, and types.

---

# COMPLETE PROJECT STRUCTURE

```text
passenger-app/

src/

├── app/
│   ├── App.tsx
│   ├── providers/
│   ├── navigation/
│   └── theme/
│
├── assets/
│
├── features/
│   ├── authentication/
│   ├── home/
│   ├── booking/
│   ├── matching/
│   ├── ride/
│   ├── wallet/
│   ├── notifications/
│   ├── profile/
│   ├── chat/
│   ├── history/
│   ├── payment/
│   ├── settings/
│   └── sos/
│
├── shared/
│   ├── components/
│   ├── hooks/
│   ├── utils/
│   ├── constants/
│   ├── types/
│   ├── services/
│   ├── validation/
│   └── animations/
│
├── api/
│
├── websocket/
│
├── storage/
│
├── maps/
│
├── analytics/
│
└── config/
```

---

# FEATURE STRUCTURE

Every feature follows the same pattern.

Example:

```text
matching/

components/

screens/

hooks/

services/

api/

types/

validation/

constants/

animations/
```

No feature should depend directly on another feature.

Use shared modules where necessary.

---

# STATE MANAGEMENT

Use modern scalable state management.

Recommended:

* Zustand (global state)
* TanStack Query (server state)
* React Context (small app-wide concerns only)

Separate responsibilities clearly.

---

# GLOBAL STATE

Store only global information.

Examples:

```text
Authenticated User

Access Token

Theme

Language

Current Ride

Current Group

Driver Info

Notification Count

App Settings
```

Avoid storing large server datasets globally.

---

# SERVER STATE

Use TanStack Query (React Query) for:

* Profile
* Ride History
* Wallet
* Notifications
* Ride Status
* Driver Details
* Matching Progress

Never manually cache API data if the query library already handles it.

---

# LOCAL COMPONENT STATE

Use local state only for:

* Input fields
* Dialog visibility
* Bottom sheet status
* Search keyword
* Temporary filters

---

# API LAYER

Never call `fetch()` directly inside screens.

Architecture:

```text
Screen
   ↓
Hook
   ↓
Service
   ↓
API Client
   ↓
FastAPI
```

---

# API CLIENT

Create one centralized HTTP client.

Responsibilities:

* Base URL
* JWT attachment
* Refresh token handling
* Timeout
* Error transformation
* Retry logic
* Logging (development)

Every request goes through it.

---

# API MODULES

Separate APIs.

```text
authApi

rideApi

matchingApi

walletApi

paymentApi

notificationApi

profileApi

chatApi

settingsApi
```

Never create one giant API file.

---

# AUTHENTICATION FLOW

```text
Splash

↓

Check Token

↓

Token Valid?

↓

YES → Home

NO → Login
```

Never trust cached login alone.

Always validate session.

---

# TOKEN MANAGEMENT

Store securely.

Requirements:

* Access Token
* Refresh Token
* Expiry Time

Auto refresh before expiry.

Logout safely if refresh fails.

---

# SPLASH SCREEN

Responsibilities:

* Load theme
* Validate session
* Initialize analytics
* Initialize FCM
* Initialize WebSocket
* Load cached configuration

Should finish quickly.

---

# HOME SCREEN DATA FLOW

When opening Home:

Parallel requests:

```text
Current Location

Profile

Saved Places

Wallet

Recent Rides

Promotions

Feature Flags
```

Do not wait for one request before starting another.

---

# BOOKING FLOW

```text
Home

↓

Destination Search

↓

Fare Estimate

↓

Booking Summary

↓

Ride Request API

↓

Matching Screen
```

---

# MATCHING FLOW

```text
Ride Created

↓

Open WebSocket

↓

Receive Matching Updates

↓

Passenger Joined

↓

Passenger Joined

↓

Passenger Left

↓

Timer Update

↓

Vote Required

↓

Driver Search

↓

Driver Assigned
```

Do not poll every few seconds.

Everything should be real-time.

---

# WEBSOCKET CONNECTION

One authenticated WebSocket.

Handle:

* Auto reconnect
* Heartbeat
* Token validation
* Re-subscription after reconnect
* Background handling

---

# WEBSOCKET EVENTS

Passenger app should listen to:

```text
MatchingProgress

PassengerJoined

PassengerLeft

GroupCompleted

VoteStarted

VoteResult

DriverSearching

DriverAssigned

OTPGenerated

DriverLocationUpdated

PickupStarted

PassengerBoarded

PassengerDropped

RideCompleted

PaymentCompleted

RideCancelled

EmergencyAlert

SystemNotification
```

---

# PUSH NOTIFICATIONS

Initialize FCM once.

Notification categories:

* Ride Updates
* Payments
* Promotions
* Support
* Security
* Wallet

Tapping a notification should deep-link to the relevant screen.

---

# GOOGLE MAPS

Maps module should manage:

* Current location
* Pickup marker
* Destination marker
* Driver marker
* Passenger route
* Polyline
* Camera movement

Keep map logic out of screens.

---

# LOCATION SERVICE

Centralize location handling.

Responsibilities:

* Permission
* Current GPS
* Accuracy
* Background updates (if needed)
* Geocoding
* Reverse geocoding

---

# OFFLINE SUPPORT

Detect:

* No internet
* Slow network
* API timeout

Show persistent banner.

Queue only safe operations.

Never queue payment requests.

---

# ERROR HANDLING

Create centralized error mapper.

Convert technical errors into user-friendly messages.

Examples:

Instead of:

```text
HTTP 500
```

Show:

```text
Something went wrong.
Please try again.
```

---

# LOADING EXPERIENCE

Never freeze UI.

Use:

* Skeleton loaders
* Progress indicators
* Shimmer cards
* Animated placeholders

Avoid blocking the entire screen unless necessary.

---

# FORM VALIDATION

Validate:

* Phone number
* OTP
* Name
* Email
* Emergency contact

Validate on client before sending.

Validate again on server.

---

# SEARCH OPTIMIZATION

Destination search should support:

* Debouncing
* Caching
* Recent searches
* Favorites
* Autocomplete

Avoid unnecessary API calls.

---

# IMAGE HANDLING

Optimize:

* Compression
* Lazy loading
* Caching
* Placeholder while loading
* Retry on failure

---

# COMPONENT HIERARCHY

Example Home Screen:

```text
HomeScreen

├── Header

├── SearchBar

├── SavedPlaces

├── RideOptions

├── Promotions

├── RecentRides

└── BottomNavigation
```

Keep components small and reusable.

---

# CUSTOM HOOKS

Create reusable hooks.

Examples:

```text
useCurrentLocation()

useCurrentRide()

useMatching()

useNotifications()

useWallet()

useProfile()

useDriverTracking()

useRideHistory()

useTheme()
```

Hooks should encapsulate logic, not UI.

---

# STORAGE

Use secure storage for:

* Tokens
* Session IDs

Use local storage only for:

* Theme
* Language
* Recent searches
* Cached settings

Never store sensitive information insecurely.

---

# FEATURE FLAGS

Passenger app should fetch feature flags from backend.

Examples:

```text
EnableChat

EnableWallet

EnableCoupons

EnableSOS

EnableDarkMode

EnablePromotions
```

Allows enabling/disabling features without updating the app.

---

# ACCESSIBILITY

Every interactive element should have:

* Accessibility label
* Accessibility hint
* Proper focus order
* Minimum touch target size

Support screen readers.

---

# PERFORMANCE

Goals:

* Cold start < 3 seconds
* Smooth scrolling
* 60 FPS animations
* Minimal unnecessary re-renders
* Lazy load heavy modules
* Memoize expensive components
* Optimize map rendering

---

# TESTING

For every feature:

* Unit tests
* Component tests
* API integration tests
* Navigation tests
* Offline tests

Critical flows (booking, payment, ride) should also have end-to-end tests.

---

# PASSENGER APP COMPLETION CHECKLIST

Before considering the Passenger App complete:

* Authentication works.
* Navigation is stable.
* Booking flow is complete.
* Matching is real-time.
* Driver assignment updates instantly.
* Common OTP is displayed.
* Live tracking works.
* Payments integrate correctly.
* Notifications function.
* Offline behavior is graceful.
* Accessibility is implemented.
* Analytics events are tracked.
* UI is responsive and polished.

No unfinished flows.

---

## END OF PART 7

**Part 8** will begin the **React Native Driver App**, covering:

* Complete architecture
* Folder structure
* Driver onboarding
* Document verification
* Online/Offline system
* Ride request lifecycle
* Common OTP verification
* Navigation
* Earnings
* Wallet
* Live tracking
* Real-time communication
* Safety
* Performance
* Full integration with the Passenger App and Ride Intelligence Engine

This will define the driver experience from registration to completing rides.
#8 
Perfect. From here onward we start the **Driver App**.

I want to point out one important improvement before continuing: after reviewing the previous parts, I think the Driver App should **not** be treated as a simple "ride receiver" like Uber. Because Traveo groups passengers first, the driver becomes an **executor of an already optimized ride plan**. That means the Driver App should be designed around executing a precomputed route rather than making decisions about matching.

---

# TRAVEO MASTER BUILD PROMPT

# PART 8 — DRIVER APP (REACT NATIVE) COMPLETE ARCHITECTURE, WORKFLOW, UI/UX & PASSENGER CONNECTION

---

# CONTEXT

Continue from Part 7.

Never redesign the Passenger App.

Never redesign Backend.

Never redesign Ride Intelligence Engine.

Driver App only executes the optimized ride generated by the Ride Intelligence Engine.

The Driver App must feel extremely simple because drivers interact with it while driving.

Safety and usability are higher priorities than feature density.

---

# DRIVER APP GOAL

The Driver App should allow drivers to:

* Register
* Verify identity
* Verify vehicle
* Go online
* Receive ride groups
* Accept/Reject requests
* Navigate to passengers
* Verify the common OTP
* Complete pickups
* Complete drop-offs
* Finish rides
* Receive payments
* View earnings
* Contact support

Nothing more should interfere while driving.

---

# DRIVER APP PRINCIPLES

The app should minimize:

* Taps
* Reading
* Typing
* Complex decisions

The Ride Intelligence Engine already made the important decisions.

The driver simply follows instructions.

---

# DRIVER APP FOLDER STRUCTURE

```text
driver-app/

src/

app/
assets/

features/

authentication/

onboarding/

vehicle/

verification/

home/

ride/

pickup/

drop/

navigation/

wallet/

earnings/

history/

notifications/

profile/

settings/

support/

shared/

components/

hooks/

services/

api/

theme/

storage/

maps/

websocket/

analytics/
```

Every feature should remain isolated.

---

# DRIVER APP DESIGN SYSTEM

Reuse the same design language as Passenger App.

However,

increase

Button size

Touch targets

Font sizes

Navigation simplicity

Contrast

Everything should be readable quickly while driving.

---

# DRIVER APP FLOW

```text
Splash
      ↓
Authentication
      ↓
Driver Verification
      ↓
Vehicle Verification
      ↓
Home Dashboard
      ↓
Go Online
      ↓
Waiting For Ride
      ↓
Ride Request
      ↓
Accept
      ↓
Navigate
      ↓
Pickup
      ↓
Ride
      ↓
Drop
      ↓
Ride Completed
      ↓
Earnings
```

---

# SPLASH SCREEN

Initialize

Authentication

Driver status

Vehicle status

WebSocket

Location

Notifications

Current ride

If driver has an active ride,

restore it immediately.

---

# LOGIN

Support

Phone OTP

Future

Email

Google

---

# PROFILE COMPLETION

Collect

Name

Photo

DOB

Emergency contact

Language

Everything editable later.

---

# DRIVER VERIFICATION

Required

Driving License

Aadhaar

PAN

Selfie

Background verification status

Verification should be performed through Admin Panel.

---

# VEHICLE REGISTRATION

Collect

Vehicle Type

Brand

Model

Color

Registration Number

Insurance

RC

Pollution Certificate

Vehicle Photos

Seat Capacity

Verification status visible.

---

# DRIVER HOME

Large

Simple

Minimal

Show only essential information.

Display

Online Status

Today's Earnings

Trips Today

Wallet

Current Incentives

Go Online button

No clutter.

---

# ONLINE / OFFLINE

Driver manually controls availability.

When Offline:

* No ride requests.
* No location sharing except minimal heartbeat if needed for account status.

When Online:

* Start sending live location.
* Eligible for ride assignment.

---

# LOCATION UPDATES

When Online:

Send GPS periodically.

Frequency should adapt:

* Higher while navigating or during rides.
* Lower while idle to save battery.

Backend validates the updates.

---

# WAITING SCREEN

Display

Current status

Searching for ride groups...

Estimated demand

Online duration

Today's completed rides

No fake countdowns.

---

# RIDE REQUEST

Unlike Uber,

the request represents a completed passenger group.

Display:

Number of passengers

Vehicle occupancy

Estimated trip distance

Estimated earnings

Pickup count

Drop count

Approximate duration

Countdown to accept

Buttons:

Accept

Reject

---

# DRIVER DECISION

If accepted:

Assign ride.

If rejected:

Notify backend immediately.

Backend finds another driver.

Driver returns to waiting state.

---

# AFTER ACCEPTANCE

Backend locks group.

Passenger App receives:

Driver assigned

Driver details

Vehicle details

ETA

Common OTP

Live location

Driver App receives:

Complete ride plan

Pickup order

Drop order

Navigation

Passenger count

---

# DRIVER DASHBOARD DURING RIDE

Show

Current destination

Current passenger

Remaining pickups

Remaining drops

ETA

Navigation

SOS

Call support

Large action button

No unnecessary information.

---

# NAVIGATION

Use Google Maps navigation.

Support

Turn-by-turn guidance

Traffic updates

Road closures

Re-routing

Driver never manually decides pickup order.

The Ride Intelligence Engine provides the sequence.

---

# PICKUP WORKFLOW

```text
Navigate

↓

Reached Pickup

↓

Passenger Confirms Identity

↓

Passenger Says Common OTP

↓

Driver Enters OTP

↓

Backend Validates

↓

Passenger Boarded

↓

Navigate To Next Pickup
```

---

# COMMON OTP

The driver **does not know** the OTP in advance.

The driver enters the OTP provided by the passenger.

Backend validates:

* Ride
* Driver
* Group
* Pickup sequence
* OTP
* Expiry

If valid:

Passenger is marked boarded.

---

# PICKUP SCREEN

Display

Passenger First Name

Pickup Address

Map

OTP Input

No Show Button

Call Passenger (privacy-preserving relay if supported)

Support Button

---

# NO SHOW

Driver taps:

Passenger not found.

Backend:

Starts configured wait timer.

If timer expires:

Mark No Show.

Passenger removed.

Fare recalculated.

Navigation updated.

---

# RIDE SCREEN

Display

Live map

Current stop

Remaining pickups

Remaining drops

Trip progress

Current earnings estimate

SOS

Support

No distractions.

---

# PASSENGER DROP

When arriving:

Driver confirms drop.

Passenger ride automatically completes.

Next destination starts immediately.

---

# LAST PASSENGER

After final drop:

Driver taps

End Ride.

Backend

Calculates final fare.

Credits earnings.

Updates analytics.

Closes ride.

---

# EARNINGS

Dashboard

Today

Yesterday

Weekly

Monthly

Lifetime

Charts

Trip count

Average rating

Average earnings

---

# WALLET

Display

Current balance

Pending payouts

Completed payouts

Bonuses

Transaction history

Withdraw requests

---

# RIDE HISTORY

Show

Route

Date

Passengers

Duration

Distance

Earnings

Receipt

Issues reported

---

# RATINGS

Driver rates each passenger individually.

Categories

Punctuality

Behavior

Cooperation

Optional comment

---

# SUPPORT

Create support tickets.

Emergency contact.

FAQ.

Chat (future).

Call support.

---

# NOTIFICATIONS

Ride assigned

Ride cancelled

Passenger no-show

Payment completed

Verification approved

Incentives

Announcements

---

# PROFILE

Photo

Vehicle

Documents

Ratings

Language

Emergency contact

Logout

---

# SETTINGS

Theme

Notifications

Location permission

Navigation preference

Language

About

Privacy

---

# DRIVER APP STATE MANAGEMENT

Use the same architectural principles as the Passenger App:

* Zustand (global app state)
* TanStack Query (server state)
* React Context only where appropriate

Keep ride execution state synchronized with backend in real time.

---

# DRIVER WEBSOCKET EVENTS

Listen for:

* RideAssigned
* RideCancelled
* PassengerCancelled
* OTPValidated
* PassengerBoarded
* PassengerNoShow
* RouteUpdated
* TrafficAlert
* RideCompleted
* PaymentCompleted
* AdminBroadcast

---

# DRIVER PERFORMANCE

Goals:

* App startup < 3 seconds
* Large touch targets
* Minimal battery drain
* Stable background GPS
* Reliable reconnection after network loss
* Smooth map rendering

---

# DRIVER SAFETY

When vehicle speed is above a configurable threshold:

* Avoid showing unnecessary pop-ups.
* Require minimal interaction.
* Defer non-critical notifications until stopped.
* Make primary ride controls large and easy to access.

Safety takes priority over feature richness.

---

# DRIVER APP COMPLETION CHECKLIST

Before considering the Driver App complete:

* Authentication works.
* Verification flow works.
* Vehicle registration works.
* Online/Offline works.
* Live location works.
* Ride requests work.
* Common OTP verification works.
* Pickup flow works.
* Drop flow works.
* Earnings update correctly.
* Wallet works.
* Ride history works.
* WebSockets remain synchronized.
* UI is optimized for driving.

---

## END OF PART 8

The next section (**Part 9**) will cover the **Admin Panel**, which is arguably the second most important application after the Passenger App. It will include:

* Complete operations dashboard
* Live ride monitoring
* Live maps
* Passenger management
* Driver verification
* Financial management
* Analytics dashboards
* AI monitoring
* Support center
* System configuration
* Feature flags
* Broadcast notifications
* Audit logs
* Role-based permissions
* Operational workflows

This panel will serve as the control center for the entire Traveo platform.
#9
Excellent. The **Admin Panel** is the operational brain of Traveo. Unlike the Passenger and Driver apps, it is used by internal teams to monitor, manage, configure, and improve the platform.

---

# TRAVEO MASTER BUILD PROMPT

# PART 9 — ADMIN PANEL (REACT) COMPLETE ARCHITECTURE, OPERATIONS, ANALYTICS & SYSTEM MANAGEMENT

---

# CONTEXT

Continue from Part 8.

Do not redesign previous modules.

The Admin Panel connects to:

* FastAPI Backend
* Ride Intelligence Engine
* Supabase
* Analytics Engine
* WebSocket Server

It should support thousands of concurrent rides and operators.

---

# PRIMARY OBJECTIVE

Create a production-grade web dashboard for internal operations.

The panel should enable administrators to:

* Monitor the platform
* Manage users
* Verify drivers
* Configure business rules
* View analytics
* Handle support
* Audit actions
* Manage finances
* Monitor ride health

Every action must be logged.

---

# ADMIN PANEL TECH STACK

Frontend

* React
* TypeScript
* Vite
* React Router
* TanStack Query
* Zustand
* WebSocket
* Google Maps

Architecture should follow the same feature-first approach used by the mobile apps.

---

# PROJECT STRUCTURE

```text
admin-panel/

src/

app/
assets/

features/

dashboard/
rides/
drivers/
passengers/
verification/
payments/
wallets/
analytics/
support/
notifications/
configuration/
roles/
audit/
reports/

shared/

components/
hooks/
api/
services/
theme/
utils/
types/
```

---

# ROLE-BASED ACCESS CONTROL (RBAC)

Supported roles:

* Super Admin
* Operations Admin
* Support Agent
* Finance Admin
* Driver Verification Officer
* Analytics Viewer
* Read-only Auditor

Permissions should be granular.

Examples:

Support Agent:

* View rides
* View users
* Respond to tickets
* Cannot modify pricing

Finance Admin:

* View payments
* Process refunds
* Export reports
* Cannot verify drivers

Super Admin:

* Full access

Never rely only on frontend permission checks. Backend must enforce authorization.

---

# ADMIN AUTHENTICATION

Support:

* Email + Password
* Multi-factor authentication (future)
* Session timeout
* Device tracking
* Login history

---

# DASHBOARD

Display real-time KPIs:

* Active rides
* Active passengers
* Online drivers
* Waiting groups
* Matching success rate
* Average wait time
* Revenue today
* Revenue this week
* Revenue this month
* Cancellation rate
* Driver acceptance rate
* Average ride occupancy

Use live updates where appropriate.

---

# LIVE MAP

Show:

* Online drivers
* Active rides
* Pickup points
* Drop points
* Ride groups
* High-demand zones

Allow filtering by:

* City
* Ride status
* Driver
* Vehicle type

---

# RIDE MANAGEMENT

View all rides.

Filters:

* Status
* Date
* Passenger
* Driver
* City
* Vehicle type

Ride details should include:

* Timeline
* Route
* Driver
* Group members
* OTP history
* Pickup events
* Drop events
* Payment details
* Logs

Allow authorized actions:

* Cancel ride
* Reassign driver
* Contact passenger
* Contact driver

---

# PASSENGER MANAGEMENT

Display:

* Profile
* Verification status (if applicable)
* Ride history
* Cancellation history
* Ratings
* Wallet
* Support tickets

Actions:

* Suspend account
* Reactivate account
* View audit logs
* Reset sessions

---

# DRIVER MANAGEMENT

Display:

* Driver profile
* Verification status
* Vehicle
* Ratings
* Earnings
* Online status
* Acceptance rate
* Cancellation rate
* Ride history

Actions:

* Approve
* Reject
* Suspend
* Reactivate
* Request additional documents

---

# DRIVER VERIFICATION

Workflow:

```text
Document Submitted
        ↓
Verification Queue
        ↓
Review
        ↓
Approve / Reject
        ↓
Notify Driver
```

Maintain a full history of verification decisions.

---

# PAYMENT MANAGEMENT

Display:

* Successful payments
* Failed payments
* Pending payments
* Refunds
* Chargebacks (future)

Allow finance admins to:

* Trigger refunds
* View invoices
* Investigate failures

---

# DRIVER PAYOUTS

Track:

* Pending payouts
* Completed payouts
* Failed payouts

Support manual review if required.

---

# WALLET MANAGEMENT

View:

* Passenger wallets
* Driver wallets

Actions:

* Credit
* Debit
* Correct balances (authorized roles only)

Every adjustment requires:

* Reason
* Operator identity
* Audit log

---

# SUPPORT CENTER

Ticket states:

* Open
* Assigned
* Waiting for user
* Resolved
* Closed

Features:

* Internal notes
* Attachments (future)
* Ride linking
* Passenger linking
* Driver linking

---

# BROADCAST NOTIFICATIONS

Allow admins to send notifications to:

* All users
* Specific city
* Passengers only
* Drivers only
* Filtered audience

Support scheduling (future).

---

# SYSTEM CONFIGURATION

Manage configurable business rules:

* Matching radius
* Matching timeout
* Vote timeout
* Driver response timeout
* OTP expiry
* Waiting charges
* Cancellation fees
* Platform commission
* Surge pricing rules
* Feature flags

Changes should take effect without redeploying the application where possible.

---

# FEATURE FLAGS

Toggle features such as:

* Chat
* Wallet
* Coupons
* SOS
* Referral program
* Promotions
* Experimental algorithms

Feature flags should support gradual rollout.

---

# ANALYTICS DASHBOARDS

Provide dashboards for:

Operational:

* Ride volume
* Wait times
* Occupancy
* Matching efficiency

Financial:

* Revenue
* Commission
* Refunds
* Driver payouts

User:

* Active users
* New registrations
* Retention
* Churn

Driver:

* Online hours
* Acceptance
* Earnings
* Ratings

Geographic:

* Heatmaps
* Popular routes
* Demand by area

---

# REPORTS

Allow exporting:

* CSV
* Excel
* PDF (future)

Reports:

* Daily
* Weekly
* Monthly
* Custom date range

---

# AUDIT LOGS

Every important admin action should be recorded:

* Login
* Logout
* Configuration changes
* Refunds
* Driver approvals
* User suspensions
* Ride cancellations
* Wallet adjustments

Each log entry should include:

* Timestamp
* User
* Role
* Action
* Previous value
* New value
* IP address (if applicable)

---

# SEARCH

Global search should locate:

* Passenger
* Driver
* Ride
* Vehicle
* Support ticket

Support fuzzy matching and partial search.

---

# REAL-TIME EVENTS

The Admin Panel should subscribe to WebSocket events:

* RideCreated
* RideMatched
* DriverAssigned
* RideStarted
* PassengerBoarded
* PassengerDropped
* RideCompleted
* PaymentCompleted
* RideCancelled
* DriverOnline
* DriverOffline
* SOSActivated

Display alerts for critical events.

---

# ALERT CENTER

Generate alerts for:

* Matching failures
* High cancellation rate
* Payment gateway failures
* Driver shortage
* Service degradation
* Surge demand
* SOS events

Allow acknowledgment and resolution tracking.

---

# SYSTEM HEALTH

Display:

* API health
* Database health
* WebSocket health
* Queue health
* Background worker health
* External service status (Maps, Payments, Notifications)

---

# PERFORMANCE

The Admin Panel should remain responsive with:

* Pagination
* Virtualized tables
* Lazy loading
* Server-side filtering
* Efficient caching

Avoid loading large datasets into the browser.

---

# SECURITY

* Enforce HTTPS
* Secure cookies or token handling
* CSRF protection where applicable
* Rate limiting
* Session expiration
* Audit every privileged action

---

# TESTING

Critical areas:

* Authentication
* Permissions
* Financial operations
* Configuration updates
* Driver verification
* Dashboard metrics
* Export functionality

---

# ADMIN PANEL COMPLETION CHECKLIST

Before considering the Admin Panel complete:

* Authentication works.
* RBAC is enforced.
* Live dashboard updates correctly.
* Ride management is functional.
* Passenger and driver management work.
* Verification workflow works.
* Payments and wallets are manageable.
* Analytics dashboards are accurate.
* Audit logs are complete.
* Feature flags function correctly.
* Alerts and system health are visible.
* Performance remains smooth under scale.

---

## END OF PART 9

**Part 10** will cover **DevOps, Infrastructure, Deployment, CI/CD, Monitoring, Security, Scalability, Backup & Disaster Recovery**, including:

* Docker architecture
* Nginx configuration
* GitHub Actions CI/CD
* Environment management
* Cloud deployment
* Load balancing
* Caching strategy
* Queue workers
* Observability (logs, metrics, tracing)
* Backup and recovery
* Scaling strategy
* Production security
* High availability
* Cost optimization

This section will define how Traveo operates reliably in production, not just how it is developed.
#10
Excellent. At this point the application architecture is essentially complete. The next step is what separates a student project from a **production-grade platform**: infrastructure, operations, security, deployment, observability, and scalability.

---

# TRAVEO MASTER BUILD PROMPT

# PART 10 — DEVOPS, INFRASTRUCTURE, CI/CD, SECURITY, MONITORING & PRODUCTION DEPLOYMENT

---

# CONTEXT

Continue from Part 9.

Do not redesign previous modules.

This section defines how Traveo runs in production.

The infrastructure should support:

* High availability
* Horizontal scalability
* Secure deployments
* Continuous delivery
* Zero-downtime updates
* Disaster recovery

---

# PRODUCTION ARCHITECTURE

```text
                    Internet
                        │
                Load Balancer
                        │
                    Nginx Proxy
                        │
        ┌───────────────┼───────────────┐
        │               │               │
 FastAPI API #1   FastAPI API #2   FastAPI API #N
        │               │               │
        └───────────────┼───────────────┘
                        │
                Background Workers
                        │
        ┌───────────────┼────────────────┐
        │               │                │
     Supabase      Redis Cache      Object Storage
        │
   PostgreSQL
```

Everything should remain stateless except the database and approved stateful services.

---

# CONTAINERIZATION

Every service should run in its own Docker container.

Examples:

* API
* Background Worker
* Nginx
* Monitoring
* Logging (optional self-hosted)
* Redis (if used)

Each container should:

* Be independently deployable
* Expose health endpoints
* Restart automatically on failure

---

# DOCKER STANDARDS

Every service should include:

* Multi-stage builds
* Small production images
* Non-root users
* Environment variables
* Health checks

Do not bake secrets into images.

---

# REVERSE PROXY

Use Nginx for:

* HTTPS termination
* Static asset delivery
* Request routing
* Compression
* Security headers
* Rate limiting (basic)
* WebSocket proxying

---

# ENVIRONMENT MANAGEMENT

Separate configurations for:

* Local
* Development
* Staging
* Production

Configuration should include:

* API URLs
* Database credentials
* JWT secrets
* Payment keys
* Maps API keys
* Notification keys
* Feature toggles

Never commit secrets to version control.

---

# CI/CD PIPELINE

Use GitHub Actions.

Pipeline stages:

```text
Code Push
      ↓
Install Dependencies
      ↓
Lint
      ↓
Run Tests
      ↓
Build
      ↓
Security Scan
      ↓
Create Docker Image
      ↓
Push Image
      ↓
Deploy
      ↓
Smoke Tests
```

Deployment should stop automatically if critical tests fail.

---

# BRANCH STRATEGY

Suggested branches:

* main
* develop
* release/*
* hotfix/*
* feature/*

Protect `main`.

Require pull requests and passing checks.

---

# CODE QUALITY

Automatically run:

* Formatting
* Linting
* Type checking (frontend)
* Static analysis
* Unit tests

Reject builds that fail quality gates.

---

# DATABASE MIGRATIONS

Use migration tooling.

Rules:

* Version every migration.
* Never edit an old migration after deployment.
* Review schema changes before production.

Support rollback where practical.

---

# BACKUPS

Automated backups:

Database:

* Daily full backups
* Point-in-time recovery if available

Object Storage:

* Regular snapshots

Configuration:

* Version-controlled infrastructure
* Backup of critical configuration

Regularly test restoration procedures.

---

# DISASTER RECOVERY

Prepare for:

* Database failure
* API failure
* Worker failure
* Region outage (future)
* Payment gateway outage
* Maps API outage

Document recovery steps.

---

# SCALING STRATEGY

FastAPI servers should scale horizontally.

API instances must remain stateless.

Background workers should scale independently.

Use autoscaling based on:

* CPU
* Memory
* Request latency
* Queue depth

---

# CACHING

Use Redis (or equivalent) for:

* Session metadata (if required)
* Feature flags cache
* Frequently accessed configuration
* Rate-limiting counters
* Temporary ride matching state (if beneficial)

Do not cache sensitive personal data unnecessarily.

---

# BACKGROUND JOBS

Move expensive work out of request-response flow.

Examples:

* Notifications
* Emails
* Analytics aggregation
* Invoice generation
* Scheduled cleanup
* Report generation

Implement retries with exponential backoff.

---

# OBSERVABILITY

Collect:

Logs

Metrics

Traces

Correlate them using request IDs.

---

# LOGGING

Structured logs only.

Include:

* Timestamp
* Request ID
* User ID (if available)
* Ride ID (if applicable)
* Severity
* Service
* Message

Avoid logging secrets or sensitive personal information.

---

# METRICS

Track:

API:

* Request count
* Error rate
* Latency
* Throughput

Ride Engine:

* Matching time
* Driver assignment time
* Average occupancy
* Cancellation rate

Business:

* Revenue
* Trips
* Active users
* Driver utilization

---

# ALERTING

Notify operators when:

* API error rate spikes
* Database unavailable
* Payment failures increase
* Matching latency exceeds threshold
* WebSocket disconnect rate rises
* Background queues grow unexpectedly

Define severity levels.

---

# HEALTH CHECKS

Expose endpoints such as:

* API health
* Database connectivity
* Queue health
* External dependency status

Load balancers should remove unhealthy instances automatically.

---

# SECURITY

Implement:

* HTTPS everywhere
* Secure JWT handling
* Strong password hashing (for applicable users)
* Input validation
* Output encoding where needed
* Security headers
* Dependency vulnerability scanning

---

# RATE LIMITING

Protect critical endpoints:

Examples:

* Login
* OTP verification
* Ride requests
* Payment APIs

Return clear error messages when limits are exceeded.

---

# API VERSIONING

Use versioned endpoints.

Example:

```text
/api/v1/...
```

Future versions should coexist during migrations.

---

# DATA PRIVACY

Principles:

* Collect only necessary data.
* Encrypt sensitive information at rest where appropriate.
* Encrypt all traffic in transit.
* Support account deletion workflows.
* Minimize retention of unnecessary logs.

---

# PAYMENT RESILIENCE

Handle:

* Duplicate webhook delivery
* Network retries
* Partial failures
* Idempotent payment processing

Never charge a passenger twice for the same ride.

---

# WEBHOOKS

Validate signatures for:

* Payment providers
* Notification providers (if applicable)

Reject unauthenticated requests.

---

# DEPENDENCY MANAGEMENT

Regularly:

* Update dependencies
* Scan for vulnerabilities
* Remove unused packages

---

# RELEASE PROCESS

Suggested flow:

```text
Feature Complete
        ↓
QA Testing
        ↓
Staging Deployment
        ↓
Acceptance Testing
        ↓
Production Deployment
        ↓
Post-release Monitoring
```

---

# ROLLBACK STRATEGY

Every deployment should support rollback.

Rollback triggers:

* Increased error rate
* Critical functionality broken
* Security issue
* Failed smoke tests

---

# TESTING STRATEGY

Automate:

Backend:

* Unit tests
* Integration tests
* API tests

Frontend:

* Component tests
* Navigation tests
* End-to-end flows

Infrastructure:

* Deployment validation
* Health checks
* Backup restoration drills

---

# PERFORMANCE TARGETS

Examples:

* App launch < 3 seconds
* API p95 latency < 300 ms (excluding third-party delays)
* Matching initiation within a few seconds under normal load
* WebSocket updates delivered promptly
* High success rate for ride assignments

These targets should be reviewed as the platform evolves.

---

# COST OPTIMIZATION

Design for efficient resource usage:

* Autoscale instead of overprovisioning
* Compress assets
* Optimize images
* Cache responsibly
* Shut down unused staging environments
* Monitor third-party API usage

---

# DOCUMENTATION

Maintain documentation for:

* Architecture
* API
* Database schema
* Deployment
* Incident response
* Runbooks
* Coding standards
* Environment setup

Documentation should be updated alongside code changes.

---

# PRODUCTION READINESS CHECKLIST

Before launching:

* CI/CD is stable.
* All environments are configured.
* Secrets are managed securely.
* Monitoring is active.
* Alerts are configured.
* Backups are verified.
* Disaster recovery is documented.
* Load testing is completed.
* Security review is completed.
* Legal and privacy requirements are reviewed.
* Release process is documented.

---

# FUTURE SCALABILITY

The architecture should support future additions without major redesign, including:

* Solo rides
* Airport rides
* Intercity rides
* Electric vehicle support
* Fleet operators
* Corporate accounts
* Ride subscriptions
* AI demand prediction
* Dynamic pricing
* Multi-city deployment
* Multi-language support
* International expansion

Design extension points rather than hardcoding assumptions.

---

## END OF PART 10

At this stage, the core architecture for Traveo is effectively complete:

* ✅ Product vision
* ✅ System architecture
* ✅ Database design
* ✅ Backend architecture
* ✅ Ride Intelligence Engine
* ✅ Passenger App
* ✅ Driver App
* ✅ Admin Panel
* ✅ Production infrastructure

The remaining sections would focus on implementation assets, such as:

* Detailed API contracts (OpenAPI-level)
* Database migration scripts
* UI component specifications
* Design tokens
* Test plans and test cases
* Sequence diagrams
* State diagrams
* ER diagrams
* User stories and acceptance criteria
* Sprint roadmap
* Coding conventions
* AI/ML model specifications for future optimization

These implementation documents can serve as the blueprint for engineering teams to build Traveo systematically.
#11
Excellent. At this point, we move from **architecture** to **engineering specifications**. These are the documents that senior engineers normally create before implementation begins.

Among the remaining sections, the **most valuable** one is the complete API specification because it becomes the contract between the Passenger App, Driver App, Admin Panel, and Backend.

---

# TRAVEO MASTER BUILD PROMPT

# PART 11 — COMPLETE API SPECIFICATION (REST + WEBSOCKET), REQUEST/RESPONSE CONTRACTS & ERROR STANDARDS

---

# CONTEXT

Continue from Part 10.

This document defines the communication contract between:

* Passenger App
* Driver App
* Admin Panel
* FastAPI Backend

Every API must be:

* Versioned
* Documented
* Consistent
* Secure
* Idempotent where appropriate

Never expose internal database structures.

---

# API DESIGN PRINCIPLES

Every endpoint should:

* Validate input
* Authenticate if required
* Authorize by role
* Return consistent responses
* Return meaningful errors
* Log requests
* Support future expansion without breaking clients

---

# API VERSIONING

Base path:

```text
/api/v1
```

Future versions:

```text
/api/v2
```

Never remove old versions immediately.

Support gradual migration.

---

# STANDARD RESPONSE FORMAT

Successful response:

```json
{
  "success": true,
  "message": "Ride created successfully.",
  "data": {},
  "meta": {}
}
```

---

Failure response:

```json
{
  "success": false,
  "message": "Invalid OTP.",
  "error": {
    "code": "INVALID_OTP",
    "details": []
  }
}
```

---

Validation error:

```json
{
  "success": false,
  "message": "Validation failed.",
  "error": {
    "code": "VALIDATION_ERROR",
    "fields": {
      "phone": "Invalid phone number"
    }
  }
}
```

Every endpoint should follow the same structure.

---

# STANDARD HTTP STATUS CODES

Use consistently.

Examples:

* 200 OK
* 201 Created
* 204 No Content
* 400 Bad Request
* 401 Unauthorized
* 403 Forbidden
* 404 Not Found
* 409 Conflict
* 422 Unprocessable Entity
* 429 Too Many Requests
* 500 Internal Server Error

Avoid returning 200 for failures.

---

# AUTHENTICATION APIs

### Register Passenger

```
POST /api/v1/auth/register
```

Request

```json
{
  "phone": "",
  "name": ""
}
```

Response

```json
{
  "userId": "",
  "otpSent": true
}
```

---

### Verify OTP

```
POST /api/v1/auth/verify-otp
```

Request

```json
{
  "phone": "",
  "otp": ""
}
```

Response

```json
{
  "accessToken": "",
  "refreshToken": "",
  "expiresIn": 3600
}
```

---

### Refresh Token

```
POST /api/v1/auth/refresh
```

---

### Logout

```
POST /api/v1/auth/logout
```

---

### Get Current User

```
GET /api/v1/auth/me
```

---

# PASSENGER PROFILE

Update profile

```
PUT /passengers/profile
```

Get profile

```
GET /passengers/profile
```

Delete account

```
DELETE /passengers/profile
```

Emergency contacts

```
GET /passengers/emergency-contacts

POST /passengers/emergency-contacts

DELETE /passengers/emergency-contacts/{id}
```

---

# SAVED PLACES

```
GET /saved-places

POST /saved-places

PUT /saved-places/{id}

DELETE /saved-places/{id}
```

---

# LOCATION

Reverse geocoding

```
POST /maps/reverse-geocode
```

Autocomplete

```
GET /maps/search
```

ETA

```
POST /maps/eta
```

Route preview

```
POST /maps/route
```

---

# RIDE REQUEST

Create ride

```
POST /rides
```

Request

```json
{
  "pickup": {},
  "destination": {},
  "rideType": "shared",
  "seats": 1
}
```

Response

```json
{
  "rideId": "",
  "matchingStarted": true
}
```

---

Cancel ride

```
POST /rides/{rideId}/cancel
```

Ride details

```
GET /rides/{rideId}
```

Ride history

```
GET /rides/history
```

---

# MATCHING

Matching status

```
GET /matching/{rideId}
```

Vote

```
POST /matching/{rideId}/vote
```

Vote request

```json
{
  "vote": "continue"
}
```

---

# DRIVER

Current driver

```
GET /rides/{rideId}/driver
```

Driver location

```
GET /rides/{rideId}/driver/location
```

---

# OTP

Get OTP

```
GET /rides/{rideId}/otp
```

Driver verify

```
POST /rides/{rideId}/verify-otp
```

---

# CHAT

Get messages

```
GET /rides/{rideId}/chat
```

Send

```
POST /rides/{rideId}/chat
```

---

# PAYMENTS

Create payment

```
POST /payments/create
```

Verify

```
POST /payments/verify
```

Invoice

```
GET /payments/{paymentId}/invoice
```

History

```
GET /payments/history
```

Refund status

```
GET /payments/refund/{refundId}
```

---

# WALLET

Balance

```
GET /wallet
```

Transactions

```
GET /wallet/transactions
```

---

# NOTIFICATIONS

```
GET /notifications
```

Mark read

```
POST /notifications/read
```

Delete

```
DELETE /notifications/{id}
```

---

# RATINGS

Submit

```
POST /rides/{rideId}/rating
```

---

# DRIVER APIs

Login

```
POST /driver/login
```

Go online

```
POST /driver/status/online
```

Go offline

```
POST /driver/status/offline
```

Accept ride

```
POST /driver/rides/{rideId}/accept
```

Reject ride

```
POST /driver/rides/{rideId}/reject
```

Passenger boarded

```
POST /driver/rides/{rideId}/boarded
```

Passenger dropped

```
POST /driver/rides/{rideId}/dropped
```

Finish ride

```
POST /driver/rides/{rideId}/complete
```

Earnings

```
GET /driver/earnings
```

---

# ADMIN APIs

Dashboard

```
GET /admin/dashboard
```

Passengers

```
GET /admin/passengers
```

Drivers

```
GET /admin/drivers
```

Approve driver

```
POST /admin/drivers/{id}/approve
```

Reject driver

```
POST /admin/drivers/{id}/reject
```

Ride management

```
GET /admin/rides
```

Cancel ride

```
POST /admin/rides/{id}/cancel
```

Configuration

```
GET /admin/configuration

PUT /admin/configuration
```

Analytics

```
GET /admin/analytics
```

Support

```
GET /admin/support

POST /admin/support/{id}/reply
```

---

# PAGINATION STANDARD

All list endpoints should support:

```
?page=1
&pageSize=20
&sortBy=
&sortOrder=
&search=
```

Response metadata:

```json
{
  "meta": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 250,
    "totalPages": 13
  }
}
```

---

# FILTERING

Support filters where applicable:

* Date range
* Ride status
* Driver
* Passenger
* City
* Vehicle type
* Payment status

---

# WEBSOCKET CONNECTION

Endpoint:

```
wss://api.traveo.com/ws
```

Authenticate during connection establishment.

One connection per client session.

---

# PASSENGER WEBSOCKET EVENTS

Server → Client

```text
MatchingStarted
PassengerJoined
PassengerLeft
VoteStarted
VoteResult
DriverSearching
DriverAssigned
OTPGenerated
DriverLocationUpdated
PickupStarted
PassengerBoarded
RideStarted
PassengerDropped
RideCompleted
PaymentCompleted
RideCancelled
NotificationReceived
SOSAcknowledged
```

---

# DRIVER WEBSOCKET EVENTS

```text
RideAssigned
RideCancelled
PassengerCancelled
PassengerNoShow
RouteUpdated
OTPVerified
RideCompleted
PaymentCompleted
NotificationReceived
```

---

# ADMIN WEBSOCKET EVENTS

```text
RideCreated
RideUpdated
DriverOnline
DriverOffline
SOSActivated
PaymentFailed
MatchingFailure
SystemAlert
```

---

# IDEMPOTENCY

Operations that may be retried should support idempotency keys.

Examples:

* Payment creation
* Refund requests
* Ride creation (if applicable)
* Wallet adjustments

---

# RATE LIMITS

Examples:

Login:

* Limited attempts per time window

OTP verification:

* Limited attempts
* Temporary lockout after repeated failures

Ride creation:

* Prevent rapid duplicate requests

---

# API DOCUMENTATION

Maintain an OpenAPI specification.

Document:

* Endpoints
* Schemas
* Authentication
* Errors
* Examples
* Rate limits

Keep documentation synchronized with implementation.

---

# API QUALITY CHECKLIST

Before releasing:

* Naming is consistent.
* Authentication is enforced.
* Authorization is enforced.
* Validation is complete.
* Pagination is standardized.
* Error responses are consistent.
* WebSocket events are documented.
* OpenAPI documentation is generated.
* Backward compatibility is considered.

---

## END OF PART 11

The remaining sections become even more implementation-oriented. The most valuable next documents are:

1. **Part 12 — Database Schema (complete SQL, indexes, constraints, RLS policies, triggers, migrations)**
2. **Part 13 — Ride Intelligence Algorithms (matching, pickup optimization, fare splitting, routing, AI models)**
3. **Part 14 — UI Component Library & Design Tokens**
4. **Part 15 — Testing Strategy, QA, User Stories & Sprint Roadmap**

These will take the project from architectural design to an implementation-ready engineering blueprint.
#12
Excellent. This is one of the most important remaining documents because it defines exactly **how the data is stored and protected**. Rather than just listing tables, this specification explains the data model, relationships, indexing, integrity rules, and security policies.

---

# TRAVEO MASTER BUILD PROMPT

# PART 12 — DATABASE IMPLEMENTATION SPECIFICATION (POSTGRESQL + SUPABASE)

---

# CONTEXT

Continue from Part 11.

Do not redesign the logical schema created earlier.

This document converts the logical database into an implementation-ready specification.

Database Platform:

* PostgreSQL (Supabase)

Goals:

* High performance
* ACID compliance
* Horizontal scalability where possible
* Secure row access
* Strong data integrity

---

# DATABASE DESIGN PRINCIPLES

Every table should:

* Use UUID primary keys
* Have `created_at`
* Have `updated_at`
* Use UTC timestamps
* Enforce foreign keys where appropriate
* Avoid duplicated data
* Be normalized unless denormalization is justified for performance

---

# NAMING CONVENTIONS

Tables:

* `snake_case`
* plural where appropriate (e.g., `ride_groups`, `wallet_transactions`)

Columns:

* `snake_case`

Foreign keys:

* `<table>_id`

Indexes:

* `idx_<table>_<column>`

Constraints:

* `chk_...`
* `fk_...`
* `uq_...`

---

# CORE TABLE GROUPS

Organize the schema into domains:

1. Identity
2. Passenger
3. Driver
4. Vehicle
5. Ride
6. Matching
7. Payments
8. Wallet
9. Notifications
10. Chat
11. Support
12. Analytics
13. Administration
14. Configuration
15. Audit

Each domain should be independently maintainable.

---

# IDENTITY DOMAIN

Core entities:

* Users
* Sessions
* Refresh Tokens
* Devices

Rules:

* One user may own multiple devices.
* Sessions should be revocable.
* Refresh tokens should be rotatable.

---

# PASSENGER DOMAIN

Store:

* Basic profile
* Saved places
* Emergency contacts
* Preferences

Relationships:

Passenger

↓

Many saved places

↓

Many rides

↓

Many ratings

Avoid storing derived statistics that can be calculated efficiently.

---

# DRIVER DOMAIN

Store:

* Driver profile
* Verification status
* Ratings
* Availability
* Online status

Separate mutable operational data (e.g., online status) from long-lived profile data where practical.

---

# VEHICLE DOMAIN

Vehicle attributes:

* Registration number
* Capacity
* Type
* Brand
* Model
* Color
* Verification status

Maintain a history of vehicle changes if drivers can replace vehicles.

---

# RIDE DOMAIN

Ride entity should contain:

* Current state
* Driver
* Ride group
* Estimated values
* Final values

Do not embed passenger details directly.

Use relationships.

---

# RIDE GROUP DOMAIN

One ride group

↓

Many members

↓

One assigned driver

↓

One common OTP

↓

One optimized route

Maintain immutable history after ride completion.

---

# MATCHING DOMAIN

Track:

* Search radius
* Matching score
* Timer
* Candidate passengers
* Final decision

Retain historical matching data for future analytics.

---

# OTP DOMAIN

Store:

* Ride reference
* OTP hash (preferred over plaintext)
* Creation time
* Expiry
* Validation status

Avoid storing plaintext OTPs longer than operationally necessary.

---

# PAYMENT DOMAIN

Separate:

* Payment
* Refund
* Invoice
* Settlement

Support retries without creating duplicate financial records.

---

# WALLET DOMAIN

Wallet:

Current balance

Transactions:

Immutable ledger entries.

Never modify historical transactions directly.

Adjustments should create new records.

---

# NOTIFICATION DOMAIN

Store:

* Recipient
* Type
* Payload reference
* Delivery status
* Read status

Support future channels:

* Push
* SMS
* Email

---

# CHAT DOMAIN

Temporary ride chat.

Entities:

* Conversation
* Participant
* Message

Messages become read-only after ride completion.

---

# SUPPORT DOMAIN

Entities:

* Ticket
* Message
* Attachment (future)

Maintain full communication history.

---

# ANALYTICS DOMAIN

Prefer event-based storage.

Examples:

* Ride created
* Passenger matched
* Driver assigned
* Ride completed
* Payment completed

Aggregate into reporting tables asynchronously.

---

# CONFIGURATION DOMAIN

Store configurable values such as:

* Matching radius
* Vote timeout
* OTP expiry
* Platform commission
* Waiting charges

Allow updates without schema changes.

---

# AUDIT DOMAIN

Every privileged action should create an immutable audit record.

Include:

* Actor
* Action
* Entity
* Timestamp
* Before value (where appropriate)
* After value (where appropriate)

---

# RELATIONSHIPS

Examples:

User

↓

Passenger Profile

↓

Ride Membership

↓

Ride Group

↓

Ride

↓

Payment

↓

Rating

Document cardinality for every relationship.

---

# INDEXING STRATEGY

Create indexes for frequently queried columns.

Examples:

Rides:

* status
* driver_id
* ride_group_id
* created_at

Drivers:

* online_status
* verification_status

Payments:

* payment_status
* created_at

Notifications:

* recipient_id
* read_status

Balance write performance against read performance.

---

# COMPOSITE INDEXES

Examples:

* `(status, created_at)`
* `(driver_id, status)`
* `(passenger_id, created_at)`

Review query plans before adding indexes.

---

# UNIQUE CONSTRAINTS

Examples:

* Phone number
* Vehicle registration number
* Government document identifiers (where stored and permitted)

---

# CHECK CONSTRAINTS

Examples:

* Rating between 1 and 5
* Seat count > 0
* Wallet balance rules (where applicable)
* Valid ride state values

---

# FOREIGN KEYS

Enforce referential integrity.

Define appropriate delete/update behavior.

Examples:

* Restrict deletion for completed financial records.
* Cascade only where safe and intentional.

---

# SOFT DELETE

Use soft deletion for entities that require historical retention.

Examples:

* Users
* Drivers
* Vehicles (if replaced)

Do not soft delete immutable financial ledger entries.

---

# ROW LEVEL SECURITY (RLS)

Passenger:

Can only access their own:

* Profile
* Wallet
* Rides
* Notifications
* Chat

Driver:

Can only access:

* Assigned rides
* Own profile
* Own earnings
* Own vehicle

Admin:

Access determined by backend authorization and service role usage.

Avoid exposing service-role credentials to clients.

---

# DATABASE FUNCTIONS

Useful database-side operations may include:

* Updating timestamps
* Maintaining audit records
* Lightweight derived values

Keep complex business logic in the backend unless there is a strong reason to move it into the database.

---

# TRIGGERS

Examples:

* Update `updated_at`
* Create audit event
* Record notification timestamp

Avoid excessive trigger complexity.

---

# TRANSACTIONS

Use database transactions for operations such as:

* Driver assignment
* Ride completion
* Payment settlement
* Wallet updates

All related changes should succeed or fail together.

---

# CONCURRENCY

Protect against race conditions.

Examples:

* Two drivers accepting the same ride
* Duplicate payment processing
* Simultaneous wallet updates

Use appropriate locking or optimistic concurrency where needed.

---

# PARTITIONING (FUTURE SCALE)

Consider partitioning large historical tables such as:

* Ride history
* Analytics events
* Audit logs
* Notifications

Partition by time where appropriate.

---

# ARCHIVING

Move historical operational data into archive storage after a defined retention period while preserving reporting capability.

---

# RETENTION

Define retention policies for:

* Logs
* Notifications
* Chat
* Analytics events
* Audit records

Retention should align with legal and business requirements.

---

# ENCRYPTION

Protect sensitive fields where appropriate.

Examples:

* Government document numbers
* Banking information
* Emergency contacts

Encrypt data in transit and use database encryption capabilities as available.

---

# IMPORT / EXPORT

Support:

* CSV export
* Administrative reporting
* Backup and restore

Exports should respect permissions and privacy rules.

---

# PERFORMANCE GUIDELINES

Target:

* Efficient indexed lookups
* Minimal full-table scans
* Controlled JOIN complexity
* Pagination for large datasets

Review slow queries regularly.

---

# MIGRATION STRATEGY

Every schema change should:

* Be versioned
* Be reversible where practical
* Be tested in staging
* Be reviewed before production

Never edit applied migrations.

---

# DATABASE TESTING

Validate:

* Constraints
* Foreign keys
* RLS policies
* Transaction behavior
* Concurrent updates
* Migration correctness

Automate database tests where feasible.

---

# DATABASE READINESS CHECKLIST

Before production:

* Schema finalized.
* Relationships validated.
* Indexes reviewed.
* Constraints implemented.
* RLS policies tested.
* Migrations versioned.
* Backup strategy verified.
* Restore process tested.
* Performance benchmarks completed.
* Security review completed.

---

## END OF PART 12

The next document (**Part 13**) is where Traveo's competitive advantage is defined. It will specify the **Ride Intelligence Algorithms**, including:

* Passenger matching algorithm
* Route overlap scoring
* Pickup optimization
* Drop optimization
* Driver ranking
* Fare splitting
* Wait-time optimization
* Cancellation handling
* No-show logic
* Future AI/ML enhancements

Unlike previous parts, this section focuses on the algorithms and decision-making logic that make Traveo different from traditional ride-hailing platforms.
#13
Excellent. This is arguably the **most valuable technical document** in the entire Traveo project. The architecture can be copied, but the **Ride Intelligence Engine algorithms** are what make Traveo unique.

One improvement before we begin: avoid embedding magic numbers (like fixed score weights or distance thresholds) directly into algorithms. Instead, every threshold, weight, timeout, and penalty should come from the configuration service so operations teams can tune the system without redeploying.

---

# TRAVEO MASTER BUILD PROMPT

# PART 13 — RIDE INTELLIGENCE ALGORITHMS, MATCHING, OPTIMIZATION & DECISION ENGINE

---

# CONTEXT

Continue from Part 12.

This document defines the algorithms used by the Ride Intelligence Engine.

Objectives:

* Maximize ride occupancy
* Minimize passenger waiting time
* Minimize driver detours
* Maximize route efficiency
* Preserve passenger experience
* Maintain fairness
* Adapt over time using historical data

All configurable values must come from backend configuration.

---

# RIDE INTELLIGENCE PIPELINE

```text id="2lhc73"
Ride Request
      ↓
Candidate Search
      ↓
Passenger Compatibility
      ↓
Route Compatibility
      ↓
Score Calculation
      ↓
Temporary Group
      ↓
Group Optimization
      ↓
Voting (if needed)
      ↓
Driver Selection
      ↓
Pickup Optimization
      ↓
Ride Monitoring
      ↓
Drop Optimization
      ↓
Fare Calculation
      ↓
Learning Feedback
```

---

# PASSENGER MATCHING ALGORITHM

## Step 1 — Candidate Discovery

Find nearby ride requests that satisfy:

* Compatible ride type
* Available seat capacity
* Similar request time window
* Geographic search radius

Exclude:

* Cancelled requests
* Assigned rides
* Expired requests
* Blocked users (if applicable)

---

## Step 2 — Compatibility Evaluation

Evaluate each candidate using configurable factors:

* Pickup proximity
* Destination proximity
* Route overlap
* Estimated delay introduced
* Vehicle capacity utilization
* Waiting time
* Traffic impact
* Accessibility requirements (future)

Reject candidates that violate hard constraints.

---

# MATCHING SCORE

Overall score should combine weighted factors.

Example conceptual formula:

```text id="2cb6f6"
Matching Score =
(Route Overlap × W1)
+
(Pickup Efficiency × W2)
+
(Destination Similarity × W3)
+
(Waiting Fairness × W4)
+
(Vehicle Utilization × W5)
-
(Additional Delay × W6)
```

Weights are configurable.

Scores should be normalized before comparison.

---

# HARD CONSTRAINTS

Never match if:

* Vehicle capacity exceeded
* Maximum pickup delay exceeded
* Maximum detour exceeded
* Ride direction incompatible
* Passenger requirements incompatible

Hard constraints always override scoring.

---

# GROUP FORMATION

Objective:

Create the highest-quality group within the configured search window.

Consider:

* Total occupancy
* Total travel efficiency
* Passenger fairness
* Average wait time

Groups remain temporary until finalized.

---

# GROUP OPTIMIZATION

When multiple candidate groups exist:

Rank them by:

1. Highest overall compatibility
2. Lowest added delay
3. Highest occupancy
4. Lowest operational cost

Do not always maximize occupancy if it significantly harms passenger experience.

---

# WAITING STRATEGY

As the timer progresses:

* Expand search radius (optional)
* Recalculate candidate groups
* Refresh scores
* Notify passengers of progress

Expansion strategy should be configurable.

---

# GROUP VOTING DECISION

If timer expires before reaching desired occupancy:

Present options:

* Continue now
* Wait longer
* Cancel

Backend evaluates votes according to configurable policy (e.g., simple majority or unanimous requirement).

---

# DRIVER SELECTION ALGORITHM

Candidate requirements:

* Online
* Verified
* Available
* Correct vehicle capacity

Score candidates using:

* ETA
* Distance
* Driver rating
* Acceptance history
* Cancellation history
* Current workload
* Expected pickup efficiency

---

# DRIVER RANKING

Conceptual scoring:

```text id="1e9b8v"
Driver Score =
ETA
+
Rating
+
Reliability
+
Route Efficiency
-
Estimated Delay
```

Support configurable weights.

---

# DRIVER ASSIGNMENT

Process:

```text id="u5ej8n"
Rank Drivers
      ↓
Offer Ride
      ↓
Accepted?
      ↓
Assign
      ↓
Lock Group
```

If rejected:

Immediately move to next ranked driver.

---

# PICKUP OPTIMIZATION

Objective:

Minimize:

* Total distance
* Pickup delay
* Driver backtracking

Inputs:

* Driver location
* Passenger locations
* Road network
* Live traffic

Outputs:

* Ordered pickup sequence
* Estimated arrival times

---

# PICKUP REOPTIMIZATION

Recalculate if:

* Passenger cancels
* Passenger no-show
* Major traffic change
* Road closure
* Driver rerouted

Do not change already completed pickups.

---

# DROPOFF OPTIMIZATION

Objective:

Minimize total travel time while maintaining fairness.

Inputs:

* Passenger destinations
* Current vehicle position
* Traffic
* Road restrictions

Produce optimized drop order.

---

# LIVE ETA ENGINE

Continuously update:

* Driver arrival
* Passenger pickup
* Passenger drop
* Ride completion

Recalculate after significant route changes.

Avoid excessive recalculation frequency.

---

# TRAFFIC ADAPTATION

Respond to:

* Congestion
* Accidents
* Road closures
* Unexpected delays

Only reroute when expected benefit exceeds configurable threshold.

---

# FAIRNESS MODEL

Protect passengers from consistently unfavorable outcomes.

Examples:

* Excessive waiting
* Repeated long detours
* Persistent last drop-offs

Incorporate fairness metrics into future matching decisions where appropriate.

---

# NO-SHOW HANDLING

Process:

```text id="4ph6ke"
Driver Arrives
      ↓
Wait Timer Starts
      ↓
Passenger Arrives?
      ↓
Yes → Continue

No → Remove Passenger
```

After removal:

* Recalculate route
* Recalculate fare
* Notify remaining passengers

---

# CANCELLATION DECISIONS

Passenger cancels before assignment:

* Remove request
* Re-optimize group

Passenger cancels after assignment:

* Apply policy
* Recalculate route if needed

Driver cancels:

* Preserve passenger group
* Restart driver selection only

---

# FARE CALCULATION

Components:

* Base fare
* Distance
* Time
* Platform fee
* Taxes
* Waiting charges
* Promotions
* Discounts

Final fare should be transparent.

---

# SHARED FARE SPLITTING

Avoid equal division.

Consider:

* Individual travel distance
* Time spent in vehicle
* Shared route proportion
* Additional detours

The total collected should equal the total ride fare after adjustments.

---

# SURGE PRICING (FUTURE)

Inputs:

* Demand
* Driver availability
* Weather
* Events
* Time of day

Rules should be configurable and capped to protect users.

---

# DYNAMIC SEARCH RADIUS

Instead of a fixed radius:

Search radius may expand gradually based on:

* Wait time
* Demand
* Time of day
* City configuration

Never expand beyond configured maximum.

---

# DEMAND PREDICTION (FUTURE AI)

Predict:

* High-demand areas
* Driver shortages
* Busy routes
* Peak times

Use predictions to improve driver positioning and matching.

---

# DRIVER REPOSITIONING (FUTURE)

Suggest high-demand areas to idle drivers based on historical demand and current trends.

Participation should remain optional.

---

# MATCH QUALITY METRICS

Track:

* Matching success rate
* Average occupancy
* Average wait time
* Additional travel time
* Cancellation rate
* Passenger satisfaction
* Driver satisfaction

Use these metrics to evaluate algorithm changes.

---

# LEARNING PIPELINE

Record outcomes for historical analysis:

* Match accepted
* Match rejected
* Ride completed
* Ride cancelled
* No-show
* Delay
* Rating

Train future optimization models using historical data rather than live production decisions.

---

# A/B TESTING SUPPORT

Allow controlled experiments for:

* Matching weights
* Search radius strategies
* Driver ranking formulas
* Notification timing

Assign users consistently to experiment groups.

Monitor key metrics before rolling out changes.

---

# ALGORITHM SAFETY

Never optimize solely for:

* Maximum occupancy
* Maximum revenue

Always maintain:

* Passenger experience
* Driver fairness
* Operational reliability

---

# CONFIGURATION

Every algorithm should obtain configurable parameters from the backend, including:

* Score weights
* Timeouts
* Distance thresholds
* Surge limits
* Waiting times
* No-show policies
* Voting rules

No hardcoded operational values.

---

# EVALUATION DASHBOARD

Expose operational metrics to the Admin Panel:

* Average matching score
* Driver assignment time
* Pickup efficiency
* Drop efficiency
* Route overlap
* Average savings
* Wait distribution
* Cancellation reasons

---

# ALGORITHM READINESS CHECKLIST

Before deployment:

* Matching constraints validated.
* Scoring configurable.
* Route optimization tested.
* Driver ranking verified.
* Fare splitting reconciles correctly.
* Edge cases covered.
* Performance benchmarked.
* Historical metrics recorded.
* A/B testing supported.
* Admin configuration integrated.

---

## END OF PART 13

At this point, Traveo's core product design and algorithms are essentially complete.

The remaining implementation documents are:

* **Part 14 — Design System & UI Component Library** (tokens, reusable components, animations, accessibility)
* **Part 15 — Testing, QA, User Stories, Sprint Plan & Development Roadmap**
* **Part 16 — AI Roadmap & Future Features** (predictive demand, personalized matching, anomaly detection, intelligent support, etc.)

These final parts transform the architecture into a complete engineering playbook for building and evolving Traveo.
#14
Excellent. This part defines **how Traveo should look and feel**. Instead of focusing on individual screens, it establishes a **single design system** that every Passenger App, Driver App, and Admin Panel component follows. This ensures consistency, accessibility, and maintainability as the product grows.

---

# TRAVEO MASTER BUILD PROMPT

# PART 14 — DESIGN SYSTEM, UI COMPONENT LIBRARY, DESIGN TOKENS & ACCESSIBILITY

---

# CONTEXT

Continue from Part 13.

Do not redesign application architecture.

This document defines the reusable visual language for:

* Passenger App
* Driver App
* Admin Panel

Every interface should be built from shared design tokens and reusable components.

---

# DESIGN PRINCIPLES

The design should be:

* Clean
* Modern
* Fast
* Accessible
* Consistent
* Minimal
* Mobile-first

Every screen should feel like part of the same product.

---

# DESIGN TOKENS

Create centralized tokens.

Never hardcode visual values throughout the application.

Token categories:

* Colors
* Typography
* Spacing
* Border Radius
* Shadows
* Elevation
* Motion
* Icons
* Breakpoints
* Z-index
* Opacity

---

# COLOR SYSTEM

Define semantic colors rather than feature-specific colors.

Examples:

* Primary
* Secondary
* Success
* Warning
* Error
* Information
* Background
* Surface
* Card
* Border
* Divider
* Disabled
* Text Primary
* Text Secondary
* Text Muted

Support:

* Light Theme
* Dark Theme
* High Contrast (future)

---

# TYPOGRAPHY SCALE

Define reusable text styles.

Examples:

* Display Large
* Display Medium
* Heading
* Title
* Subtitle
* Body Large
* Body
* Caption
* Label
* Button

Use consistent line heights and font weights.

Avoid arbitrary font sizes.

---

# SPACING SYSTEM

Use a consistent spacing scale.

Example units:

```text id="spacing-scale"
4
8
12
16
20
24
32
40
48
64
80
96
```

All layouts should derive spacing from this scale.

---

# BORDER RADIUS

Create reusable values.

Examples:

* Extra Small
* Small
* Medium
* Large
* Extra Large
* Full (pill/circle)

---

# SHADOW & ELEVATION

Define levels:

* Level 0 (none)
* Level 1 (cards)
* Level 2 (dialogs)
* Level 3 (bottom sheets)
* Level 4 (floating actions)

Keep shadows subtle and consistent.

---

# ICONOGRAPHY

Use a single icon family.

Rules:

* Consistent stroke width
* Consistent sizing
* Semantic icon usage
* Support accessibility labels

---

# MOTION SYSTEM

Animations should communicate state changes.

Examples:

* Screen transitions
* Bottom sheet expansion
* Button press feedback
* Loading indicators
* Ride matching progress
* Driver arrival updates

Animations should be smooth and purposeful.

---

# COMPONENT LIBRARY

Every component should be reusable, documented, and independently testable.

---

# BUTTONS

Variants:

* Primary
* Secondary
* Tertiary
* Outline
* Text
* Destructive
* Loading
* Disabled

Support:

* Icons
* Full width
* Compact

---

# INPUT COMPONENTS

Support:

* Text
* Phone
* OTP
* Search
* Password (future where needed)
* Multiline

Features:

* Validation
* Error messages
* Helper text
* Prefix/Suffix icons

---

# MAP COMPONENTS

Reusable components:

* Pickup Marker
* Destination Marker
* Driver Marker
* Passenger Marker
* Route Polyline
* ETA Card

Keep map rendering logic separate from business logic.

---

# CARDS

Card types:

* Ride Card
* Driver Card
* Passenger Group Card
* Wallet Card
* Promotion Card
* Notification Card

Cards should share consistent spacing and elevation.

---

# LIST COMPONENTS

Reusable lists:

* Ride History
* Notifications
* Saved Places
* Transactions
* Support Tickets

Support:

* Infinite scrolling
* Empty states
* Loading states
* Error states

---

# DIALOGS

Reusable dialogs:

* Confirmation
* Warning
* Success
* Error
* Permission request

Avoid creating custom dialog styles for each feature.

---

# BOTTOM SHEETS

Use for:

* Ride details
* Driver details
* Saved places
* Payment methods
* Filters

Maintain consistent heights and gestures.

---

# FEEDBACK COMPONENTS

Support:

* Snackbar
* Toast
* Inline Alert
* Banner
* Progress Indicator

Differentiate informational, success, warning, and error messages visually.

---

# LOADING STATES

Provide:

* Skeleton loaders
* Progress bars
* Activity indicators
* Placeholder cards

Avoid blank screens while data loads.

---

# EMPTY STATES

Every list should define an empty state.

Include:

* Illustration (optional)
* Title
* Description
* Primary action (if applicable)

---

# ERROR STATES

Every recoverable error should include:

* Clear explanation
* Retry option
* Contact support (when appropriate)

Avoid exposing technical error details.

---

# NAVIGATION PATTERNS

Use consistent navigation:

* Bottom tabs
* Stack navigation
* Modal presentation
* Bottom sheets

Back navigation should always behave predictably.

---

# RESPONSIVE DESIGN

Support:

* Small phones
* Large phones
* Tablets (future)
* Desktop (Admin Panel)

Avoid fixed widths where unnecessary.

---

# ACCESSIBILITY

Meet modern accessibility standards.

Requirements:

* Screen reader labels
* Focus management
* Keyboard navigation (Admin Panel)
* Sufficient color contrast
* Large touch targets
* Dynamic text scaling support

---

# INTERNATIONALIZATION

Prepare for:

* Multiple languages
* RTL layouts (future)
* Locale-specific date, time, and currency formatting

Do not hardcode display text.

---

# THEME MANAGEMENT

Centralized theme provider.

Support:

* Light
* Dark
* System preference

Theme changes should update the entire application consistently.

---

# DESIGN DOCUMENTATION

For every component, document:

* Purpose
* Props/API
* States
* Accessibility considerations
* Usage examples
* Do's and Don'ts

Maintain documentation alongside the codebase.

---

# COMPONENT TESTING

Each reusable component should have:

* Unit tests
* Visual regression tests (where practical)
* Accessibility checks
* Interaction tests

---

# DESIGN SYSTEM GOVERNANCE

Establish contribution rules:

* No duplicate components
* New components require documentation
* Design review before addition
* Deprecation policy for obsolete components

---

# DESIGN QUALITY CHECKLIST

Before release:

* Tokens are centralized.
* Components are reusable.
* Themes work correctly.
* Accessibility requirements are met.
* Responsive layouts verified.
* Loading, empty, and error states implemented.
* Motion is smooth and purposeful.
* Documentation is complete.

---

## END OF PART 14

The final major document is **Part 15 — Testing Strategy, QA, User Stories, Sprint Planning & Development Roadmap**. It will describe:

* End-to-end testing strategy
* Unit, integration, and performance testing
* User stories with acceptance criteria
* Development phases
* Sprint-by-sprint roadmap
* Release milestones
* Definition of Done
* Risk register
* Project governance
* Engineering workflow

This serves as the execution plan that takes Traveo from specification to a production-ready product.
Excellent. This is the **final major engineering document**. It answers **how the team builds, tests, releases, and maintains Traveo** from day one through production.

One recommendation after reviewing all previous parts: don't try to build everything at once. Even though the architecture supports a large platform, the implementation roadmap should prioritize a usable shared-ride product first, then progressively add advanced features.

---

# TRAVEO MASTER BUILD PROMPT

# PART 15 — TESTING STRATEGY, QA, USER STORIES, SPRINT PLANNING & DEVELOPMENT ROADMAP

---

# CONTEXT

Continue from Part 14.

Do not redesign previous architecture.

This document defines how Traveo is engineered from development through production.

Objectives:

* Deliver incrementally
* Maintain quality
* Reduce regressions
* Support continuous delivery
* Ensure production readiness

---

# DEVELOPMENT METHODOLOGY

Recommended approach:

* Agile
* Scrum
* Two-week sprints
* Continuous Integration
* Continuous Delivery

Each sprint should produce working software.

---

# PHASED DELIVERY

## Phase 1 — Foundation

Deliver:

* Project setup
* Authentication
* Database
* Backend foundation
* Passenger App shell
* Driver App shell
* Admin authentication
* CI/CD
* Monitoring basics

Deliverable:

Users can sign in and basic infrastructure is operational.

---

## Phase 2 — Core Ride Flow

Implement:

* Ride booking
* Passenger matching
* Group formation
* Driver assignment
* Common OTP
* Live tracking
* Ride completion

Deliverable:

End-to-end shared rides function.

---

## Phase 3 — Payments

Implement:

* Razorpay
* Wallet
* Fare calculation
* Ride history
* Ratings
* Invoices

Deliverable:

Complete commercial ride flow.

---

## Phase 4 — Operations

Implement:

* Admin dashboard
* Driver verification
* Analytics
* Notifications
* Support center

Deliverable:

Operational platform.

---

## Phase 5 — Optimization

Implement:

* Better matching
* AI insights
* Feature flags
* Performance improvements
* Additional analytics

Deliverable:

Production optimization.

---

# USER STORIES

Every feature should begin with user stories.

Example:

Passenger

> As a passenger, I want to request a shared ride so that I can travel at a lower cost.

Acceptance Criteria:

* Pickup selected
* Destination selected
* Fare estimate shown
* Ride request submitted
* Matching begins

---

Driver

> As a driver, I want to receive optimized ride groups so I can complete trips efficiently.

Acceptance Criteria:

* Ride request received
* Accept/reject works
* Navigation starts
* OTP verification succeeds

---

Admin

> As an operations administrator, I want to monitor active rides in real time.

Acceptance Criteria:

* Dashboard updates
* Live map works
* Ride details accessible

---

# DEFINITION OF READY (DoR)

A task is ready when:

* Requirements understood
* UI available (if applicable)
* API contract defined
* Dependencies identified
* Acceptance criteria written
* Estimates completed

---

# DEFINITION OF DONE (DoD)

A feature is done only when:

* Code complete
* Code reviewed
* Tests passing
* Documentation updated
* Accessibility checked
* Performance acceptable
* Security reviewed
* Analytics added
* Error handling implemented
* Merged successfully

---

# TESTING PYRAMID

Prioritize:

```text id="testing-pyramid"
End-to-End
────────────
Integration
────────────
Unit Tests
```

Focus on many unit tests, fewer integration tests, and targeted end-to-end tests.

---

# UNIT TESTING

Backend:

* Services
* Repositories
* Utility functions
* Validation
* Algorithms

Frontend:

* Hooks
* Components
* State management
* Utility functions

Target high coverage for critical business logic.

---

# INTEGRATION TESTING

Verify interactions between:

* API ↔ Database
* Backend ↔ Payment provider
* Backend ↔ Maps
* Backend ↔ Notifications
* Backend ↔ WebSocket

---

# END-TO-END TESTING

Critical scenarios:

Passenger:

* Register
* Login
* Book ride
* Matching
* Ride completion
* Payment
* Rating

Driver:

* Login
* Go online
* Accept ride
* Pickup
* OTP
* Drop
* Earnings

Admin:

* Login
* Approve driver
* Monitor ride
* Issue refund
* Update configuration

---

# PERFORMANCE TESTING

Measure:

* API latency
* Concurrent users
* WebSocket scalability
* Matching performance
* Database query speed

Conduct load and stress testing before major releases.

---

# SECURITY TESTING

Test:

* Authentication
* Authorization
* SQL injection resistance
* XSS (Admin Panel)
* CSRF (where applicable)
* JWT handling
* Rate limiting
* Sensitive data exposure

---

# ACCESSIBILITY TESTING

Verify:

* Screen readers
* Keyboard navigation
* Contrast ratios
* Focus indicators
* Touch target sizes
* Dynamic font scaling

---

# DEVICE TESTING

Passenger & Driver Apps:

* Android (multiple versions)
* iOS (future if supported)
* Small and large screens
* Low-memory devices
* Poor network conditions

Admin Panel:

* Chrome
* Edge
* Firefox
* Safari

---

# REGRESSION TESTING

Before every release:

* Booking
* Matching
* Driver assignment
* OTP
* Payments
* Notifications
* Ride completion

Maintain an automated regression suite.

---

# RELEASE CHECKLIST

Before deployment:

* Tests pass
* Security scan passes
* Migrations reviewed
* Monitoring enabled
* Rollback prepared
* Release notes written

---

# BUG MANAGEMENT

Severity:

* Critical
* High
* Medium
* Low

Track:

* Root cause
* Fix
* Verification
* Regression prevention

---

# SPRINT STRUCTURE

Suggested two-week sprint:

Days 1–2:

* Planning
* Design clarification

Days 3–8:

* Development

Days 9–10:

* Testing
* Bug fixing

Day 11:

* Code freeze

Day 12:

* Release candidate

Day 13:

* Sprint review

Day 14:

* Retrospective

---

# ROADMAP (HIGH LEVEL)

## Milestone 1

Foundation complete.

Success criteria:

* Apps launch
* Authentication works
* Infrastructure operational

---

## Milestone 2

Ride booking complete.

Success criteria:

* Shared rides can be requested

---

## Milestone 3

Ride execution complete.

Success criteria:

* Passenger matched
* Driver assigned
* OTP verified
* Ride completed

---

## Milestone 4

Payments live.

Success criteria:

* Real payments
* Wallet
* Ratings

---

## Milestone 5

Operations complete.

Success criteria:

* Admin panel functional
* Monitoring active
* Support available

---

## Milestone 6

Production launch.

Success criteria:

* Stability targets achieved
* Monitoring healthy
* Documentation complete

---

# ENGINEERING STANDARDS

Every pull request should include:

* Clear description
* Linked issue
* Test evidence
* Screenshots (UI changes)
* Migration notes (if applicable)

Require at least one reviewer before merge.

---

# DOCUMENTATION

Maintain:

* API documentation
* Architecture diagrams
* Database documentation
* Deployment guide
* Coding standards
* Runbooks
* Incident response procedures

Documentation should evolve with the code.

---

# RISK REGISTER

Track major risks such as:

* Low driver availability
* Matching quality degradation
* Payment gateway outages
* External API limits
* GPS inaccuracies
* Traffic data quality
* Security vulnerabilities

Define mitigation plans for each.

---

# SUCCESS METRICS

Technical:

* API latency
* Crash rate
* Error rate
* Test pass rate

Business:

* Matching success
* Ride completion
* Average occupancy
* Passenger satisfaction
* Driver satisfaction
* Revenue
* Retention

Operational:

* Mean time to detect incidents
* Mean time to recover
* Support resolution time

---

# CONTINUOUS IMPROVEMENT

After every release:

* Review metrics
* Review customer feedback
* Analyze incidents
* Prioritize improvements
* Refine algorithms
* Update documentation

---

# FINAL PROJECT READINESS CHECKLIST

Before public launch:

* Architecture implemented.
* Backend stable.
* Passenger App production-ready.
* Driver App production-ready.
* Admin Panel production-ready.
* Monitoring operational.
* Security reviewed.
* Documentation complete.
* Performance targets met.
* Disaster recovery verified.
* Support processes established.

---

## END OF PART 15

### COMPLETE TRAVEO MASTER ARCHITECTURE STATUS

You now have a comprehensive blueprint covering:

* ✅ Part 1–3: Vision, architecture, technology stack, and database design
* ✅ Part 4–5: Backend architecture and Ride Intelligence Engine
* ✅ Part 6–8: Passenger App and Driver App
* ✅ Part 9: Admin Panel
* ✅ Part 10: Infrastructure, DevOps, deployment, monitoring, and security
* ✅ Part 11–13: API contracts, database implementation, and ride algorithms
* ✅ Part 14: Design system and UI component library
* ✅ Part 15: Testing, QA, roadmap, and engineering process

This provides a complete engineering blueprint that can guide the development of Traveo from initial implementation through production and future evolution.
#16
Excellent. Although Part 15 completed the original blueprint, there is one document that is still missing—and it's the one most startups create before writing code.

If Traveo were being built by a team at Uber, Google, or a funded startup, this would exist as the **Product Requirements Document (PRD)**. It translates the engineering architecture into a product specification that designers, engineers, QA, and stakeholders all work from.

---

# TRAVEO MASTER BUILD PROMPT

# PART 16 — PRODUCT REQUIREMENTS DOCUMENT (PRD), MVP STRATEGY & FUTURE ROADMAP

---

# CONTEXT

Continue from Part 15.

This document defines **what** Traveo should achieve from a product perspective.

It should guide:

* Product Managers
* Designers
* Backend Engineers
* Mobile Engineers
* QA Engineers
* Operations Team
* Future Investors

---

# PRODUCT VISION

## Mission

Enable affordable, efficient, and intelligent shared transportation by grouping passengers with similar routes before assigning a driver.

---

## Vision Statement

Traveo aims to become the default shared mobility platform by maximizing vehicle occupancy while minimizing passenger waiting time, travel cost, and environmental impact.

---

# PROBLEM STATEMENT

Current ride-hailing platforms primarily optimize for:

* Fast driver assignment
* Individual passenger convenience

This often results in:

* Low vehicle occupancy
* Higher passenger costs
* More traffic
* Increased emissions
* Driver idle time

Traveo addresses this by optimizing passenger grouping before driver assignment.

---

# TARGET USERS

## Primary

Urban commuters who:

* Travel daily
* Prefer lower costs
* Are willing to share rides
* Use smartphones regularly

---

## Secondary

Drivers seeking:

* Better vehicle utilization
* Higher occupancy
* Predictable routes
* Reduced idle time

---

## Tertiary

Operations teams needing:

* Real-time visibility
* Configurable business rules
* Efficient support workflows

---

# VALUE PROPOSITION

Passengers receive:

* Lower fares
* Intelligent matching
* Transparent ride progress
* Shared savings

Drivers receive:

* Optimized passenger groups
* Reduced idle time
* Better route efficiency

Platform receives:

* Higher utilization
* Better scalability
* Rich operational analytics

---

# CORE PRODUCT PRINCIPLES

1. Passenger-first decisions.
2. Transparent ride lifecycle.
3. Fairness for passengers and drivers.
4. Safety by default.
5. Configurable business rules.
6. Data-driven optimization.

---

# MVP SCOPE

The first production version should include:

Passenger App:

* Authentication
* Ride booking
* Shared ride matching
* Live ride tracking
* Payments
* Ratings

Driver App:

* Authentication
* Verification
* Ride execution
* OTP verification
* Earnings

Admin Panel:

* Dashboard
* Ride monitoring
* Driver verification
* User management
* Basic analytics

Backend:

* Matching engine
* Driver assignment
* Fare calculation
* Notifications

---

# OUT OF SCOPE (MVP)

These features should be deferred:

* Airport rides
* Rentals
* Corporate accounts
* Referral program
* Loyalty program
* Dynamic pricing
* AI demand prediction
* Voice assistant
* EV fleet optimization
* Multi-country support

The architecture should remain extensible for these additions.

---

# PRODUCT SUCCESS METRICS

Passenger:

* Ride request success rate
* Average wait time
* Average savings
* Ride completion rate
* Repeat usage
* App rating

Driver:

* Online utilization
* Acceptance rate
* Earnings per hour
* Cancellation rate
* Rating

Platform:

* Daily active users
* Monthly active users
* Ride occupancy
* Revenue
* Matching success rate
* Support resolution time

---

# KEY USER JOURNEYS

## Passenger

Open App

↓

Choose destination

↓

Request shared ride

↓

Matched with passengers

↓

Driver assigned

↓

Receive OTP

↓

Complete ride

↓

Pay

↓

Rate

---

## Driver

Login

↓

Go online

↓

Receive ride group

↓

Accept

↓

Navigate

↓

Pickup passengers

↓

Verify OTP

↓

Complete route

↓

Receive earnings

---

## Admin

Login

↓

Monitor rides

↓

Resolve issues

↓

Verify drivers

↓

Review analytics

↓

Adjust configuration

---

# NON-FUNCTIONAL REQUIREMENTS

Performance:

* Responsive UI
* Stable real-time updates
* Efficient API responses

Reliability:

* High availability
* Safe retries
* Graceful degradation

Security:

* Strong authentication
* Role-based authorization
* Encrypted communication

Scalability:

* Multi-city support
* Horizontal backend scaling
* Configurable infrastructure

---

# RISKS

Technical:

* Matching quality
* GPS accuracy
* Third-party dependency failures

Operational:

* Low driver supply
* Fraud
* Payment disputes

Business:

* Passenger adoption
* Driver acquisition
* Regulatory compliance

Each risk should have a mitigation strategy documented separately.

---

# LAUNCH CRITERIA

Before public launch:

* End-to-end ride flow validated
* Payments functioning
* Monitoring active
* Driver verification process operational
* Support team trained
* Documentation complete

---

# POST-LAUNCH PRIORITIES

After launch, prioritize improvements based on data.

Potential areas:

* Faster matching
* Better route optimization
* Enhanced notifications
* Driver incentives
* UI refinements

---

# FUTURE PRODUCT ROADMAP

## Version 1.x

* Improve matching
* Expand analytics
* Enhance support tools

---

## Version 2.x

* Dynamic pricing
* AI-assisted driver positioning
* Personalized ride recommendations
* Improved demand forecasting

---

## Version 3.x

* Multi-city operations
* Corporate travel
* Fleet partnerships
* Subscription plans

---

## Version 4.x

* Autonomous vehicle readiness (future)
* Carbon impact reporting
* Advanced multimodal transportation integration

---

# PRODUCT GOVERNANCE

Establish ownership for:

* Product
* Engineering
* Design
* QA
* Operations
* Customer Support

Review metrics regularly and update priorities based on measurable outcomes rather than assumptions.

---

# FINAL PRODUCT CHECKLIST

The product is considered launch-ready when:

* Users can complete the full ride lifecycle.
* Drivers can execute rides reliably.
* Admins can monitor and manage operations.
* Payments settle correctly.
* Real-time updates remain synchronized.
* Monitoring and alerting are active.
* Documentation is current.
* Customer support processes are in place.

---

# TRAVEO EVOLUTION PRINCIPLE

Every future feature should satisfy at least one of the following:

* Improves passenger experience
* Improves driver experience
* Improves operational efficiency
* Improves safety
* Improves scalability
* Improves profitability

If a feature does not clearly support one of these goals, reconsider its priority.

---

## END OF PART 16

### COMPLETE TRAVEO BLUEPRINT

With Parts **1–16**, you now have a comprehensive specification covering:

* Product vision and strategy
* Technical architecture
* Backend systems
* Database
* Ride Intelligence Engine
* Passenger, Driver, and Admin applications
* API contracts
* Design system
* Infrastructure
* Security
* Testing
* Engineering process
* Product requirements and roadmap

This is sufficient to begin implementation in a structured, phased manner while leaving room for future growth and iteration.
Yes. The core architecture is complete, but if you wanted a **startup-grade specification** like what companies maintain internally, there are still a few valuable documents that can sit on top of Parts 1–16.

I would add them in this order:

---

# PART 17 — SECURITY ARCHITECTURE & THREAT MODEL

Purpose:
Design Traveo to be secure from the beginning instead of adding security later.

Contents:

* Authentication architecture
* JWT lifecycle
* Refresh token rotation
* RBAC (Role-Based Access Control)
* Permission matrix
* Threat modeling (STRIDE)
* OWASP Top 10 mitigations
* SQL Injection prevention
* XSS/CSRF protection
* Rate limiting
* API abuse protection
* Bot detection
* Device trust
* Encryption at rest
* Encryption in transit
* Secrets management
* Key rotation
* Audit logging
* Fraud detection
* Account recovery
* Incident response
* Security monitoring
* Vulnerability management
* Penetration testing plan

---

# PART 18 — OBSERVABILITY & SITE RELIABILITY ENGINEERING (SRE)

Purpose:
Ensure Traveo can be monitored and operated reliably in production.

Contents:

* Logging strategy
* Metrics collection
* Distributed tracing
* Health checks
* SLIs
* SLOs
* Error budgets
* Incident management
* Alert routing
* Dashboards
* Capacity planning
* Auto scaling
* Disaster recovery
* Backup verification
* Chaos engineering
* Runbooks
* On-call procedures
* Root cause analysis

---

# PART 19 — FRAUD DETECTION & TRUST ENGINE

Purpose:
Protect the platform from abuse.

Contents:

* Fake account detection
* GPS spoofing detection
* Fake ride detection
* Driver collusion
* Payment fraud
* Wallet abuse
* OTP abuse
* Promotion abuse
* Device fingerprinting
* Velocity checks
* Risk scoring
* Trust score
* Automatic account restrictions
* Manual review workflow

---

# PART 20 — AI & MACHINE LEARNING PLATFORM

Purpose:
Future intelligence layer.

Contents:

* Demand prediction
* ETA prediction
* Driver positioning
* Passenger clustering
* Cancellation prediction
* Dynamic pricing (future)
* Personalized ride suggestions
* Churn prediction
* Recommendation engine
* Model lifecycle
* Offline training
* Online inference
* Feature store
* Experiment tracking
* Model monitoring

---

# PART 21 — LEGAL, PRIVACY & COMPLIANCE

Purpose:
Prepare for real-world deployment.

Contents:

* Privacy policy requirements
* Terms of service
* Data retention
* GDPR readiness
* India DPDP Act considerations
* Consent management
* Cookie policy (Admin/Web)
* Data deletion workflow
* Right to access/export data
* Data anonymization
* Law enforcement requests
* Compliance audit process

---

# PART 22 — BUSINESS OPERATIONS PLAYBOOK

Purpose:
Run Traveo as a business.

Contents:

* City launch checklist
* Driver onboarding
* Passenger onboarding
* Marketing operations
* Referral campaigns
* Support workflows
* Pricing operations
* Surge policy
* Driver incentives
* Customer retention
* Financial reconciliation
* KPI reviews
* Operations dashboards

---

# PART 23 — ENGINEERING HANDBOOK

Purpose:
Standardize development practices.

Contents:

* Repository structure
* Branching strategy
* Commit conventions
* Code review guidelines
* Coding standards
* Architecture Decision Records (ADRs)
* Dependency management
* API versioning policy
* Feature flag policy
* Documentation standards
* Release management
* Deprecation policy

---

# PART 24 — INVESTOR & SCALING STRATEGY

Purpose:
Prepare Traveo for fundraising and growth.

Contents:

* Market opportunity
* Competitive analysis
* Business model
* Revenue streams
* Cost structure
* Unit economics
* Go-to-market strategy
* Expansion plan
* Funding roadmap
* Financial projections
* Key risks
* Exit scenarios

---

## Overall Assessment

Your original **Parts 1–16** are sufficient to build and launch Traveo.

**Parts 17–24** are not required to write the software, but they make the project much closer to what a well-funded startup would maintain:

* **Parts 1–16:** Complete engineering blueprint (≈95% of what developers need).
* **Parts 17–24:** Operational, security, business, and scaling documentation (the remaining ≈5%) that helps run, secure, and grow the product after launch.

With all 24 parts, you'd have documentation spanning product, engineering, operations, security, compliance, and business strategy.