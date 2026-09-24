# 🚕 Traveo — College-Verified Shared Mobility Platform

> **Hackathon Submission & Web Demo Guide**
>
> Traveo is a college-exclusive, passenger-first shared ride platform. Unlike traditional taxi aggregators where a single passenger books a full vehicle, **Traveo groups verified students from the same college heading in the same direction first, splits the fare equitably by travel distance, and then dispatches nearby auto-rickshaws and cabs.**

---

## 🌟 Key Features

- 🎓 **Strict Same-College Matching:** Only verified students belonging to the same campus can see, join, and share rides.
- 💰 **Automated Fair Fare Splitting:** Fares are split proportionally based on each student's exact travel distance.
- 🛡️ **Safety-First Dispatch:** Ride creator holds the starting OTP; every joiner gets a student matching verification ID.
- 🗺️ **Interactive Real-Time Map & Routing:** Live routing, route polylines, pickup/drop pins, and moving driver location markers.
- ⚡ **Multi-Role Web Demo:** Passenger App, Driver App, Multi-Student Isolation Tester, and Admin Operations Dashboard all runnable in standard web browsers.

---

## 💻 Hackathon Web Quickstart (Run Everything in Web)

To test the entire Traveo ecosystem on your computer using web browsers, you will open **3 to 4 terminals**. Follow the step-by-step instructions below.

### 📋 Prerequisites

Ensure you have installed on your computer:
- **Node.js**: `v18+` or `v20+` ([Download Node.js](https://nodejs.org/))
- **Python**: `3.11+` or `3.12+` ([Download Python](https://www.python.org/))
- **Git**

Clone the repository and enter the folder:
```bash
git clone https://github.com/Dnyaneshh18/Traveo.git
cd Traveo
```

Install the root Node dependencies once:
```bash
npm install
```

---

## 🖥️ Terminal 1: Backend Server (FastAPI + SQLite/PostgreSQL)

This terminal powers the REST APIs, WebSockets, real-time driver dispatch, and student verification.

```bash
cd backend

# 1. Create a virtual environment
python -m venv .venv

# 2. Activate the virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# 3. Upgrade pip and install backend dependencies
python -m pip install --upgrade pip
pip install -e .

# 4. Start the FastAPI server on port 8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Backend API URL**: `http://localhost:8000`
- **Interactive Swagger API Docs**: `http://localhost:8000/docs`

---

## 🖥️ Terminal 2: Passenger App (Student Web Interface)

This is the passenger application where students verify their college ID, create rides from/to campus, view active shared rides, and track driver progress.

```bash
cd Traveo

# Run Passenger App on Web (Port 8081)
npm run passenger:web
```

- **Passenger Web App URL**: [http://localhost:8081](http://localhost:8081)
- **Demo Student Login**:
  - **Phone**: `9822000001` or `9811119999` (or enter your own 10-digit number)
  - **OTP**: `123456` *(Default dev OTP)*
  - **Select College**: Choose **VIT Pune**, **COEP**, or any partner college.

---

## 🖥️ Terminal 3: Driver App (Auto-Rickshaw & Cab Web Interface)

This is the driver partner application where drivers go online, receive incoming ride offers with instant fare & route previews, verify passenger OTPs, and complete trips.

```bash
cd Traveo

# Run Driver App on Web (Port 8082)
npm run driver:web
```

- **Driver Web App URL**: [http://localhost:8082](http://localhost:8082)
- **Demo Driver Logins**:
  - **Phone**: `9900000001` (Ramesh Pawar - Auto Rickshaw, near campus)
  - **Phone**: `9900000002` (Suresh Patil - Auto Rickshaw)
  - **Phone**: `9900000003` (Santosh Shinde - Prime Sedan Cab)
  - **OTP**: `123456`

---

## 🖥️ Terminal 4: Admin Operations & College Dashboard

The command center for college administrators and platform managers to monitor live campus rides, student approvals, verified drivers, and platform dispatch configuration.

```bash
cd Traveo

# Run Admin Dashboard (Port 5173)
npm run admin
```

- **Admin Portal URL**: [http://localhost:5173](http://localhost:5173)
- **Admin Credentials**:
  - **Email**: `admin@traveo.app`
  - **Password**: `Admin@123`

---

## 🧪 Optional: Multi-Student Isolation Tester

To verify that students from College A (e.g. VIT Pune) **never** see rides posted by students from College B (e.g. COEP), a dedicated multi-student tester is available:

```bash
cd Traveo
python -m http.server 8083 --directory apps/passenger-tester
```
- Open [http://localhost:8083](http://localhost:8083) to simulate two distinct students side-by-side and witness real-time same-college isolation in action.

---

## 🎬 Recommended 3-Minute Hackathon Demo Flow

1. **Open Driver App** (`http://localhost:8082`):
   - Login with `9900000001` and OTP `123456`.
   - Tap **"GO ONLINE"**.
2. **Open Passenger App** (`http://localhost:8081`):
   - Login with `9822000001` and OTP `123456`.
   - Tap **"Post a ride"**, choose **Leaving Campus**, enter a destination (e.g., `Swargate` or `Pune Station`).
   - View the dynamic route preview, fare estimate, and tap **"Publish ride"**.
   - Tap **"Lock & Request Driver"**.
3. **Witness Instant Dispatch**:
   - The Driver App (`http://localhost:8082`) instantly chimes and pops up the ride request with route, seats, and fare.
   - Click **"Accept"**.
   - The Passenger App immediately switches to the live trip screen with the approaching driver's details and real-time pickup status!
4. **Inspect Admin Dashboard** (`http://localhost:5173`):
   - View the active ride reflected on the live operations map.

---

## 📁 Repository Structure

```text
Traveo/
├── apps/
│   ├── passenger-app/       # Student React Native/Web application (Port 8081)
│   ├── driver-app/          # Driver React Native/Web partner app (Port 8082)
│   ├── admin-panel/         # React + Vite admin dashboard (Port 5173)
│   └── passenger-tester/    # Multi-student isolation testing suite (Port 8083)
├── backend/
│   ├── app/
│   │   ├── intelligence/    # Dispatch ring algorithm, route grouping & fare splitting
│   │   ├── modules/         # Auth, Rides, Drivers, Colleges, Ratings
│   │   ├── realtime/        # WebSocket live hub for location & events
│   │   └── main.py          # FastAPI application entrypoint (Port 8000)
│   └── pyproject.toml       # Backend Python dependencies
└── packages/
    ├── shared/              # Shared types, API clients, pricing models & constants
    └── mobile-ui/           # Unified cross-platform UI kit & map components
```

---

## 📜 License & Acknowledgments

Built for hackathons and campus mobility innovation.
All rights reserved © 2026 Traveo Team.
