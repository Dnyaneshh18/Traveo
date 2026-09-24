# 🚕 Traveo — College-Verified Shared Mobility Platform

> **Hackathon Submission & Complete Zero-to-One Local Setup Guide**
>
> Traveo is a college-exclusive, passenger-first shared ride platform. Unlike traditional taxi aggregators where a single passenger books a full vehicle, **Traveo groups verified students from the same college heading in the same direction first, splits the fare equitably by travel distance, and then dispatches nearby auto-rickshaws and cabs.**

---

## 🌟 Key Features

- 🎓 **Strict Same-College Matching:** Only verified students belonging to the same campus can see, join, and share rides.
- 💰 **Automated Fair Fare Splitting:** Fares are split proportionally based on each student's exact travel distance.
- 🛡️ **Safety-First Dispatch:** Ride creator holds the starting OTP; every joiner gets a student matching verification ID.
- 🗺️ **Interactive Real-Time Map & Routing:** Live routing, route polylines, pickup/drop pins, and moving driver location markers.
- ⚡ **Full Web Browser Demo:** Passenger App, Driver App, Multi-Student Isolation Tester, and Admin Operations Dashboard all runnable in standard web browsers with zero mobile compilation required.

---

## 📋 Complete Prerequisites (Install Before Running)

If you are setting up this project on a fresh computer (or extracting it from a `.zip` archive), make sure you have the following installed:

### 1. Node.js (v18.x, v20.x, or v22.x LTS)
- Download & install from: **[https://nodejs.org/](https://nodejs.org/)**
- Verify in your terminal:
  ```bash
  node -v
  npm -v
  ```

### 2. Python (v3.11 or v3.12)
- Download & install from: **[https://www.python.org/downloads/](https://www.python.org/downloads/)**
- ⚠️ **Crucial on Windows**: Check the box **"Add python.exe to PATH"** during installation.
- Verify in your terminal:
  ```bash
  python --version
  ```

### 3. Git (Optional, if cloning from GitHub)
- Download & install from: **[https://git-scm.com/](https://git-scm.com/)**

---

## 🚀 One-Time Setup (First Time Opening the Project)

Open your terminal or PowerShell in the root project folder (`Traveo`):

### Step 1: Install Node Dependencies
Run once from the root folder:
```bash
npm install
```
*(This installs all root and workspace dependencies for the Passenger App, Driver App, Admin Panel, and shared libraries).*

### Step 2: Set Up Backend Python Environment
```bash
cd backend

# Create a virtual environment named .venv
python -m venv .venv

# Activate the virtual environment:
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# (If PowerShell says script execution is disabled, run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass, then re-run the script)
# On macOS / Linux:
# source .venv/bin/activate

# Upgrade pip and install the backend package & dependencies:
python -m pip install --upgrade pip
pip install -e .

# Return to root directory
cd ..
```

---

## 🖥️ How to Run the Project (Terminal by Terminal)

To experience the full live system, open **4 terminal windows** side-by-side:

```
┌─────────────────────────────────┬─────────────────────────────────┐
│  TERMINAL 1: FastAPI Backend    │  TERMINAL 2: Student Passenger  │
│  Port 8000 (REST & WebSockets)  │  Port 8081 (Web App)            │
├─────────────────────────────────┼─────────────────────────────────┤
│  TERMINAL 3: Driver Partner     │  TERMINAL 4: Admin Operations   │
│  Port 8082 (Web App)            │  Port 5173 (Vite Dashboard)     │
└─────────────────────────────────┴─────────────────────────────────┘
```

---

### 🖥️ Terminal 1: Backend Server (FastAPI + SQLite/PostgreSQL)
Powers authentication, ride matching algorithms, distance calculations, and real-time WebSocket events.

```bash
cd backend

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Mac/Linux:
# source .venv/bin/activate

# Start backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Backend API URL**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

### 🖥️ Terminal 2: Student Passenger App (Port 8081)
Where students sign in with their college profile, post rides, browse fellow students' rides, and track active trips.

```bash
# In the Traveo root directory:
npm run passenger:web
```
- **URL**: [http://localhost:8081](http://localhost:8081)
- **Demo Student Login**:
  - **Phone**: `9822000001` or `9811119999` (or any 10-digit number)
  - **OTP**: `123456` *(Default dev code)*
  - **College**: Choose **VIT Pune**, **COEP**, or any listed campus.

---

### 🖥️ Terminal 3: Driver Partner App (Port 8082)
Where auto-rickshaw and cab drivers go online, receive incoming group requests, verify ride OTPs, and navigate trips.

```bash
# In the Traveo root directory:
npm run driver:web
```
- **URL**: [http://localhost:8082](http://localhost:8082)
- **Demo Driver Login**:
  - **Phone**: `9900000001` (Ramesh Pawar - Auto Rickshaw, near campus)
  - **Phone**: `9900000002` (Suresh Patil - Auto Rickshaw)
  - **Phone**: `9900000003` (Santosh Shinde - Prime Sedan Cab)
  - **OTP**: `123456`

---

### 🖥️ Terminal 4: Admin Operations Dashboard (Port 5173)
The live operations command center for colleges and city dispatchers.

```bash
# In the Traveo root directory:
npm run admin
```
- **URL**: [http://localhost:5173](http://localhost:5173)
- **Admin Credentials**:
  - **Email**: `admin@traveo.app`
  - **Password**: `Admin@123`

---

## 🎬 3-Minute Hackathon Demo Script (How to Present)

Follow this sequence to showcase the platform smoothly to judges:

1. **Open Driver App** ([http://localhost:8082](http://localhost:8082)):
   - Sign in as Ramesh (`9900000001` / OTP `123456`).
   - Switch the toggle to **"GO ONLINE"**. The driver is now visible to the dispatch engine.
2. **Open Passenger App** ([http://localhost:8081](http://localhost:8081)):
   - Sign in as a student (`9822000001` / OTP `123456`).
   - Click **"Post a ride"**, select **"Leaving Campus"**, and enter a destination (e.g. `Swargate` or `Pune Station`).
   - Show judges the dynamic route polyline, per-seat price breakdown, and tap **"Publish ride"**.
   - Tap **"Lock & Request Driver"**.
3. **Show Instant Automated Dispatch**:
   - Flip to the Driver App window — it instantly chimes with an audio alert and displays the incoming offer popup with pickup location, rider count, and guaranteed earnings.
   - Click **"Accept"**.
   - Flip back to the Passenger App — the screen instantly switches to the active trip state, displaying the driver's vehicle number, live arrival distance, and start OTP!
4. **Show Admin Operations** ([http://localhost:5173](http://localhost:5173)):
   - Show the live operations map displaying current active rides, student verifications, and fleet status.

---

## 🧪 Testing Same-College Privacy & Isolation

To demonstrate to judges that students from different colleges **never** see each other's rides:

1. In a terminal, run:
   ```bash
   python -m http.server 8083 --directory apps/passenger-tester
   ```
2. Open [http://localhost:8083](http://localhost:8083).
3. The tester opens two mock student screens side-by-side:
   - **Student A** (VIT Pune) posts a ride to Swargate.
   - **Student B** (COEP) searches the feed.
   - **Result**: Student B's feed remains completely empty, verifying 100% same-college isolation and campus privacy.

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

## 📜 License & Hackathon Notes

Built for hackathon demonstration and campus shared mobility innovation.
All rights reserved © 2026 Traveo Team.
