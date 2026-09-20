/**
 * Traveo API Client — Real Backend Communication Service
 * Connects Passenger App to FastAPI Backend
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface LocationInput {
  latitude: number;
  longitude: number;
  address?: string;
}

export type VehicleCategoryType =
  | 'auto_rickshaw'
  | 'sedan_4_seater'
  | 'suv_6_8_seater';

export interface BookRidePayload {
  pickup: LocationInput;
  destination: LocationInput;
  requested_seats: number;
  vehicle_category?: VehicleCategoryType;
  ride_type?: 'shared' | 'solo';
}

class ApiService {
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

  // 1. Register Passenger / Request OTP
  async registerPassenger(phone: string, name: string = 'Passenger', age?: number) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ phone, name, age }),
    });
    
    if (response.status === 409) {
      throw new Error("This mobile number is already registered.");
    }
    if (!response.ok) {
      throw new Error("Registration failed.");
    }
    return await response.json();
  }

  // 1.5. Login Passenger
  async loginPassenger(phone: string) {
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

  // 2. Verify OTP & Obtain JWT
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

  // 3. Current User Profile
  async getCurrentUser() {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 4. Book Shared Ride
  async bookRide(payload: BookRidePayload) {
    const response = await fetch(`${API_BASE_URL}/rides/book`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    return await response.json();
  }

  // 5. Cancel Ride Request
  async cancelRide(requestId: string) {
    const response = await fetch(`${API_BASE_URL}/rides/${requestId}/cancel`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return response.ok;
  }

  // 6. Active Ride
  async getActiveRide() {
    const response = await fetch(`${API_BASE_URL}/rides/active`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 7. Group Vote
  async voteInGroup(groupId: string, vote: 'continue' | 'wait' | 'cancel') {
    const response = await fetch(`${API_BASE_URL}/rides/group/${groupId}/vote`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ vote }),
    });
    return await response.json();
  }

  // 8. Ride History
  async getRideHistory(limit = 20, offset = 0) {
    const response = await fetch(`${API_BASE_URL}/rides/history?limit=${limit}&offset=${offset}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 9. Wallet Balance
  async getWallet() {
    const response = await fetch(`${API_BASE_URL}/payments/wallet`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 10. Submit Rating
  async submitRating(rideId: string, ratedId: string, rating: number, review?: string) {
    const response = await fetch(`${API_BASE_URL}/ratings`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        ride_id: rideId,
        rated_id: ratedId,
        rating,
        review,
      }),
    });
    return await response.json();
  }
}

export const apiService = new ApiService();
