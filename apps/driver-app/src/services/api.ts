/**
 * Traveo Driver API Client — Backend Communication Service
 * Connects Driver App to FastAPI Backend
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

class DriverApiService {
  private token: string | null = null;

  setAuthToken(token: string) {
    this.token = token;
  }

  getAuthToken() {
    return this.token;
  }

  private getHeaders() {
    return {
      'Content-Type': 'application/json',
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
    };
  }

  // 1. Register Driver / Request OTP
  async registerDriver(
    phone: string,
    firstName: string,
    lastName: string = '',
    age?: number,
    vehicleCategory?: string,
    plateNumber?: string,
    aadhaarNumber?: string,
    licenseNumber?: string
  ) {
    const response = await fetch(`${API_BASE_URL}/auth/register/driver`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        phone,
        first_name: firstName,
        last_name: lastName,
        age,
        vehicle_category: vehicleCategory,
        plate_number: plateNumber,
        aadhaar_number: aadhaarNumber,
        license_number: licenseNumber
      }),
    });
    
    if (response.status === 409) {
      throw new Error("This mobile number is already registered.");
    }
    if (!response.ok) {
      throw new Error("Registration failed.");
    }
    return await response.json();
  }

  // 1.5. Login Driver
  async loginDriver(phone: string) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ phone }),
    });

    if (response.status === 404) {
      throw new Error("Account not found. Please register first.");
    }
    if (!response.ok) {
      throw new Error("Login failed.");
    }
    return await response.json();
  }

  // 2. Verify OTP & Obtain JWT Token
  async verifyOtp(phone: string, otp: string) {
    const response = await fetch(`${API_BASE_URL}/auth/verify-otp`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ phone, otp }),
    });
    const data = await response.json();
    if (data.access_token) {
      this.setAuthToken(data.access_token);
    }
    return data;
  }

  // 3. Go Online
  async goOnline() {
    const response = await fetch(`${API_BASE_URL}/driver/go-online`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 4. Go Offline
  async goOffline() {
    const response = await fetch(`${API_BASE_URL}/driver/go-offline`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 5. Update Real-time Location
  async updateLocation(latitude: number, longitude: number, heading?: number, speed?: number) {
    const response = await fetch(`${API_BASE_URL}/driver/update-location`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ latitude, longitude, heading, speed }),
    });
    return response.ok;
  }

  // 6. Accept Ride
  async acceptRide() {
    const response = await fetch(`${API_BASE_URL}/driver/accept-ride`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 7. Reject Ride
  async rejectRide() {
    const response = await fetch(`${API_BASE_URL}/driver/reject-ride`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 8. Verify Passenger OTP
  async verifyOtpCode(rideId: string, otp: string) {
    const response = await fetch(`${API_BASE_URL}/driver/rides/${rideId}/verify-otp`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ otp }),
    });
    return await response.json();
  }

  // 9. Pickup Passenger
  async pickupPassenger(rideId: string, passengerId: string) {
    const response = await fetch(`${API_BASE_URL}/driver/rides/${rideId}/pickup`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ passenger_id: passengerId }),
    });
    return await response.json();
  }

  // 10. Start Ride
  async startRide(rideId: string) {
    const response = await fetch(`${API_BASE_URL}/driver/rides/${rideId}/start`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 11. Drop Passenger
  async dropPassenger(rideId: string, passengerId: string) {
    const response = await fetch(`${API_BASE_URL}/driver/rides/${rideId}/drop`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ passenger_id: passengerId }),
    });
    return await response.json();
  }

  // 12. Complete Ride
  async completeRide(rideId: string) {
    const response = await fetch(`${API_BASE_URL}/driver/rides/${rideId}/complete`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 13. Active Ride
  async getActiveRide() {
    const response = await fetch(`${API_BASE_URL}/driver/active-ride`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 14. Driver Earnings Summary
  async getEarnings() {
    const response = await fetch(`${API_BASE_URL}/payments/driver/earnings`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return await response.json();
  }
}

export const driverApiService = new DriverApiService();
