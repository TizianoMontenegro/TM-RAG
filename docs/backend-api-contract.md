# TM-Backend API Contract for TM-RAG

> **Purpose**: Internal API endpoints that TM-Backend must expose for TM-RAG's Agentic
> pipeline to consume. These are **not** the same endpoints the frontend uses — they are
> purpose-built for the RAG agent and may return flattened or denormalized data optimized
> for LLM context.
>
> **Base URL**: `http://tm-backend:8000` (configured via `BACKEND_API_URL`)
>
> **Authentication**: All requests include `Authorization: Bearer <TM_RAG_API_KEY>`.
> TM-Backend validates this token and identifies TM-RAG as the caller.

---

## 1. Get User Profile

Returns the user's profile information and loyalty status. Used when the RAG agent needs
to personalize responses or verify the user's identity.

```
GET /api/v1/rag/users/{user_id}/
```

**Path Parameters**

| Parameter | Type   | Description          |
|-----------|--------|----------------------|
| `user_id` | string | TM Airlines user ID  |

**Response `200 OK`**

```json
{
  "user_id": "usr_abc123",
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Mbeki",
  "phone": "+27821234567",
  "loyalty_program": {
    "tier": "gold",
    "member_since": "2021-03-15",
    "miles_balance": 84200
  },
  "preferences": {
    "language": "en",
    "seat_preference": "window",
    "meal_preference": "vegetarian",
    "communication_email": true,
    "communication_sms": false
  }
}
```

**Field Reference**

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | Stable user identifier |
| `email` | string | Primary email address |
| `first_name` | string | Given name |
| `last_name` | string | Family name |
| `phone` | string \| null | Contact phone number |
| `loyalty_program.tier` | string | One of: `"bronze"`, `"silver"`, `"gold"`, `"platinum"` |
| `loyalty_program.member_since` | string | ISO 8601 date (`YYYY-MM-DD`) |
| `loyalty_program.miles_balance` | integer | Current redeemable miles |
| `preferences` | object | User travel preferences (nullable if none set) |

**Error Responses**

| Status | Body | Condition |
|--------|------|-----------|
| `401` | `{"detail": "Invalid or expired token"}` | Bad auth token |
| `404` | `{"detail": "User not found"}` | `user_id` does not exist |

---

## 2. List User Bookings

Returns all bookings for a user. The agent uses this when the user asks about their
trips, upcoming flights, or booking history without specifying a booking ID.

```
GET /api/v1/rag/users/{user_id}/bookings/
```

**Query Parameters**

| Parameter | Type    | Default | Description |
|-----------|---------|---------|-------------|
| `status`  | string  | `"all"` | Filter by status: `"all"`, `"upcoming"`, `"completed"`, `"cancelled"` |
| `limit`   | integer | `10`    | Max results to return (1–50) |
| `offset`  | integer | `0`     | Pagination offset |

**Path Parameters**

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `user_id` | string | TM Airlines user ID |

**Response `200 OK`**

```json
{
  "bookings": [
    {
      "booking_id": "BK20250710A001",
      "status": "confirmed",
      "created_at": "2025-07-01T14:30:00Z",
      "flight": {
        "flight_number": "TM456",
        "departure_airport": "JNB",
        "arrival_airport": "CPT",
        "departure_time": "2025-07-15T08:00:00Z",
        "arrival_time": "2025-07-15T10:15:00Z"
      },
      "passengers": 2,
      "total_price": {
        "amount": 4520.00,
        "currency": "ZAR"
      }
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

**Field Reference**

| Field | Type | Description |
|-------|------|-------------|
| `bookings[].booking_id` | string | Unique booking reference |
| `bookings[].status` | string | One of: `"confirmed"`, `"pending"`, `"cancelled"`, `"completed"` |
| `bookings[].created_at` | string | ISO 8601 datetime |
| `bookings[].flight.flight_number` | string | Airline flight code |
| `bookings[].flight.departure_airport` | string | IATA airport code |
| `bookings[].flight.arrival_airport` | string | IATA airport code |
| `bookings[].flight.departure_time` | string | ISO 8601 datetime |
| `bookings[].flight.arrival_time` | string | ISO 8601 datetime |
| `bookings[].passengers` | integer | Number of passengers on this booking |
| `bookings[].total_price.amount` | number | Total cost |
| `bookings[].total_price.currency` | string | ISO 4217 currency code |
| `total` | integer | Total bookings matching filter (for pagination) |
| `limit` | integer | Requested limit |
| `offset` | integer | Requested offset |

**Error Responses**

| Status | Body | Condition |
|--------|------|-----------|
| `401` | `{"detail": "Invalid or expired token"}` | Bad auth token |
| `404` | `{"detail": "User not found"}` | `user_id` does not exist |

---

## 3. Get Booking Details

Returns full details of a single booking, including passenger manifests, seat
assignments, and ancillary purchases. Used when the agent needs specific booking
information (e.g., "What seat am I in on flight TM456?").

```
GET /api/v1/rag/bookings/{booking_id}/
```

**Path Parameters**

| Parameter    | Type   | Description            |
|--------------|--------|------------------------|
| `booking_id` | string | TM Airlines booking ID |

**Query Parameters**

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `user_id` | string | **Required.** Ownership verification — endpoint returns 404 if the booking does not belong to this user |

**Response `200 OK`**

```json
{
  "booking_id": "BK20250710A001",
  "status": "confirmed",
  "created_at": "2025-07-01T14:30:00Z",
  "flight": {
    "flight_number": "TM456",
    "departure_airport": "JNB",
    "arrival_airport": "CPT",
    "departure_time": "2025-07-15T08:00:00Z",
    "arrival_time": "2025-07-15T10:15:00Z",
    "aircraft": "Airbus A320",
    "gate": "B12",
    "terminal": "B"
  },
  "passengers": [
    {
      "name": "Alice Mbeki",
      "seat": "14A",
      "seat_class": "economy",
      "meal": "vegetarian",
      "checked_bags": 1,
      "carry_on_bags": 1
    },
    {
      "name": "John Mbeki",
      "seat": "14B",
      "seat_class": "economy",
      "meal": "standard",
      "checked_bags": 2,
      "carry_on_bags": 1
    }
  ],
  "ancillaries": [
    {
      "type": "extra_baggage",
      "description": "1 extra checked bag (23kg)",
      "price": { "amount": 350.00, "currency": "ZAR" }
    },
    {
      "type": "travel_insurance",
      "description": "Basic travel insurance",
      "price": { "amount": 120.00, "currency": "ZAR" }
    }
  ],
  "total_price": {
    "amount": 4520.00,
    "currency": "ZAR"
  },
  "payment_status": "paid"
}
```

**Field Reference**

| Field | Type | Description |
|-------|------|-------------|
| `booking_id` | string | Unique booking reference |
| `status` | string | One of: `"confirmed"`, `"pending"`, `"cancelled"`, `"completed"` |
| `created_at` | string | ISO 8601 datetime |
| `flight.flight_number` | string | Airline flight code |
| `flight.departure_airport` | string | IATA code |
| `flight.arrival_airport` | string | IATA code |
| `flight.departure_time` | string | ISO 8601 datetime |
| `flight.arrival_time` | string | ISO 8601 datetime |
| `flight.aircraft` | string | Aircraft type (e.g., "Airbus A320") |
| `flight.gate` | string \| null | Departure gate (assigned close to departure) |
| `flight.terminal` | string \| null | Terminal identifier |
| `passengers[].name` | string | Full passenger name |
| `passengers[].seat` | string \| null | Seat assignment (null if not yet assigned) |
| `passengers[].seat_class` | string | One of: `"economy"`, `"premium_economy"`, `"business"`, `"first"` |
| `passengers[].meal` | string | Meal selection |
| `passengers[].checked_bags` | integer | Number of checked bags |
| `passengers[].carry_on_bags` | integer | Number of carry-on bags |
| `ancillaries[]` | array | Purchased add-ons (empty array if none) |
| `ancillaries[].type` | string | One of: `"extra_baggage"`, `"travel_insurance"`, `"seat_upgrade"`, `"priority_boarding"`, `"lounge_access"` |
| `ancillaries[].description` | string | Human-readable description |
| `total_price.amount` | number | Total booking cost |
| `total_price.currency` | string | ISO 4217 currency code |
| `payment_status` | string | One of: `"paid"`, `"pending"`, `"refunded"`, `"partial_refund"` |

**Error Responses**

| Status | Body | Condition |
|--------|------|-----------|
| `401` | `{"detail": "Invalid or expired token"}` | Bad auth token |
| `404` | `{"detail": "Booking not found"}` | `booking_id` does not exist or does not belong to `user_id` |

---

## 4. Get Flight Status

Returns real-time status for a specific flight. Used when the user asks about
delays, gate changes, or current flight state.

```
GET /api/v1/rag/flights/{flight_number}/status/
```

**Path Parameters**

| Parameter       | Type   | Description              |
|-----------------|--------|--------------------------|
| `flight_number` | string | Airline flight code      |

**Query Parameters**

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `date`    | string | Optional. ISO 8601 date (`YYYY-MM-DD`). Disambiguates when a flight number operates on multiple dates. Defaults to today. |

**Response `200 OK`**

```json
{
  "flight_number": "TM456",
  "date": "2025-07-15",
  "status": "on_time",
  "departure": {
    "airport": "JNB",
    "scheduled_time": "2025-07-15T08:00:00Z",
    "estimated_time": "2025-07-15T08:00:00Z",
    "actual_time": null,
    "gate": "B12",
    "terminal": "B"
  },
  "arrival": {
    "airport": "CPT",
    "scheduled_time": "2025-07-15T10:15:00Z",
    "estimated_time": "2025-07-15T10:15:00Z",
    "actual_time": null
  },
  "delay_minutes": 0,
  "aircraft": "Airbus A320",
  "last_updated": "2025-07-15T06:30:00Z"
}
```

**Field Reference**

| Field | Type | Description |
|-------|------|-------------|
| `flight_number` | string | Airline flight code |
| `date` | string | ISO 8601 date |
| `status` | string | One of: `"scheduled"`, `"boarding"`, `"departed"`, `"in_air"`, `"landed"`, `"arrived"`, `"cancelled"`, `"diverted"`, `"delayed"` |
| `departure.airport` | string | IATA code |
| `departure.scheduled_time` | string | ISO 8601 datetime |
| `departure.estimated_time` | string \| null | ISO 8601 datetime (null if no estimate) |
| `departure.actual_time` | string \| null | ISO 8601 datetime (null until departed) |
| `departure.gate` | string \| null | Current gate assignment |
| `departure.terminal` | string \| null | Terminal |
| `arrival.airport` | string | IATA code |
| `arrival.scheduled_time` | string | ISO 8601 datetime |
| `arrival.estimated_time` | string \| null | ISO 8601 datetime |
| `arrival.actual_time` | string \| null | ISO 8601 datetime (null until landed) |
| `delay_minutes` | integer | Current delay in minutes (0 if on time) |
| `aircraft` | string | Aircraft type |
| `last_updated` | string | ISO 8601 datetime — when this status was last refreshed |

**Error Responses**

| Status | Body | Condition |
|--------|------|-----------|
| `401` | `{"detail": "Invalid or expired token"}` | Bad auth token |
| `404` | `{"detail": "Flight not found"}` | No flight matching `flight_number` on the given `date` |

---

## 5. Get Loyalty Status

Returns the user's full loyalty program details, including tier benefits and
recent mile activity. Used when the agent answers questions like
"What are my gold tier benefits?" or "How many miles do I have?"

```
GET /api/v1/rag/users/{user_id}/loyalty/
```

**Path Parameters**

| Parameter | Type   | Description         |
|-----------|--------|---------------------|
| `user_id` | string | TM Airlines user ID |

**Response `200 OK`**

```json
{
  "user_id": "usr_abc123",
  "tier": "gold",
  "member_since": "2021-03-15",
  "miles_balance": 84200,
  "miles_expiring_soon": {
    "amount": 12000,
    "expiry_date": "2025-12-31"
  },
  "tier_benefits": [
    "Priority check-in",
    "Extra 10kg checked baggage allowance",
    "Lounge access at OR Tambo International",
    "Priority boarding"
  ],
  "recent_activity": [
    {
      "date": "2025-07-01",
      "description": "Flight TM456 JNB-CPT",
      "miles_earned": 1200,
      "type": "flight"
    },
    {
      "date": "2025-06-15",
      "description": "Redeemed for lounge access",
      "miles_earned": -2500,
      "type": "redemption"
    }
  ]
}
```

**Field Reference**

| Field | Type | Description |
|-------|------|-------------|
| `tier` | string | One of: `"bronze"`, `"silver"`, `"gold"`, `"platinum"` |
| `member_since` | string | ISO 8601 date |
| `miles_balance` | integer | Current redeemable miles |
| `miles_expiring_soon.amount` | integer | Miles expiring on `expiry_date` (0 if none) |
| `miles_expiring_soon.expiry_date` | string \| null | ISO 8601 date |
| `tier_benefits` | string[] | List of benefits for current tier |
| `recent_activity` | array | Last 10 mile transactions |
| `recent_activity[].date` | string | ISO 8601 date |
| `recent_activity[].description` | string | Human-readable description |
| `recent_activity[].miles_earned` | integer | Positive = earned, negative = redeemed |
| `recent_activity[].type` | string | One of: `"flight"`, `"partner"`, `"promotion"`, `"redemption"` |

**Error Responses**

| Status | Body | Condition |
|--------|------|-----------|
| `401` | `{"detail": "Invalid or expired token"}` | Bad auth token |
| `404` | `{"detail": "User not found"}` | `user_id` does not exist |

---

## 6. Search Flights

Search available flights between two airports. Used when the agent helps users
find alternative flights (e.g., "Are there later flights from JNB to CPT today?").

```
GET /api/v1/rag/flights/search/
```

**Query Parameters**

| Parameter     | Type    | Required | Description |
|---------------|---------|----------|-------------|
| `origin`      | string  | Yes      | IATA departure airport code |
| `destination` | string  | Yes      | IATA arrival airport code |
| `date`        | string  | Yes      | ISO 8601 date (`YYYY-MM-DD`) |
| `passengers`  | integer | No       | Number of passengers (default: `1`) |
| `seat_class`  | string  | No       | One of: `"economy"`, `"premium_economy"`, `"business"`, `"first"` |

**Response `200 OK`**

```json
{
  "flights": [
    {
      "flight_number": "TM456",
      "departure_time": "2025-07-15T08:00:00Z",
      "arrival_time": "2025-07-15T10:15:00Z",
      "duration_minutes": 135,
      "aircraft": "Airbus A320",
      "available_seats": {
        "economy": 42,
        "business": 4
      },
      "price": {
        "amount": 2260.00,
        "currency": "ZAR",
        "per_passenger": true
      }
    },
    {
      "flight_number": "TM460",
      "departure_time": "2025-07-15T14:00:00Z",
      "arrival_time": "2025-07-15T16:10:00Z",
      "duration_minutes": 130,
      "aircraft": "Boeing 737-800",
      "available_seats": {
        "economy": 88,
        "business": 8
      },
      "price": {
        "amount": 1980.00,
        "currency": "ZAR",
        "per_passenger": true
      }
    }
  ],
  "search_criteria": {
    "origin": "JNB",
    "destination": "CPT",
    "date": "2025-07-15",
    "passengers": 1,
    "seat_class": null
  }
}
```

**Field Reference**

| Field | Type | Description |
|-------|------|-------------|
| `flights[].flight_number` | string | Airline flight code |
| `flights[].departure_time` | string | ISO 8601 datetime |
| `flights[].arrival_time` | string | ISO 8601 datetime |
| `flights[].duration_minutes` | integer | Flight duration in minutes |
| `flights[].aircraft` | string | Aircraft type |
| `flights[].available_seats` | object | Seat availability by class (key = class, value = count) |
| `flights[].price.amount` | number | Price per passenger |
| `flights[].price.currency` | string | ISO 4217 currency code |
| `flights[].price.per_passenger` | boolean | Always `true` for this endpoint |
| `search_criteria` | object | Echo of the request parameters |

**Error Responses**

| Status | Body | Condition |
|--------|------|-----------|
| `400` | `{"detail": "Missing required parameter: origin"}` | Required query param missing |
| `401` | `{"detail": "Invalid or expired token"}` | Bad auth token |
| `404` | `{"detail": "No flights found"}` | No flights match the criteria |

---

## Authentication

All endpoints require a `Bearer` token in the `Authorization` header:

```
Authorization: Bearer <TM_RAG_API_KEY>
```

TM-Backend validates this token against its service account registry. The token
identifies the caller as TM-RAG and determines which user records are accessible.

**Token behavior**:
- TM-RAG passes `user_id` as a parameter — TM-Backend verifies the token is
  authorized to access that user's data (service-to-service trust).
- Tokens are long-lived and rotated via TM-Backend's `create_rag_service_user` command.
- Revoked tokens return `401 Unauthorized` on every endpoint.

---

## Error Response Shape

All error responses follow a consistent shape:

```json
{
  "detail": "Human-readable error message safe for the RAG agent to relay to the user"
}
```

- `detail` is user-facing — the RAG agent may include it in its response to the end user.
- Do not include stack traces, SQL errors, or internal identifiers in `detail`.
- TM-RAG wraps HTTP errors from these endpoints as `AgentException` with:
  - `message`: A generic fallback ("Booking information is temporarily unavailable.")
  - `detail`: The original HTTP error string (logged only, never sent to the user)

---

## Endpoint Summary

| # | Method | Path | Purpose |
|---|--------|------|---------|
| 1 | `GET` | `/api/v1/rag/users/{user_id}/` | User profile & preferences |
| 2 | `GET` | `/api/v1/rag/users/{user_id}/bookings/` | List all user bookings |
| 3 | `GET` | `/api/v1/rag/bookings/{booking_id}/` | Full booking details |
| 4 | `GET` | `/api/v1/rag/flights/{flight_number}/status/` | Real-time flight status |
| 5 | `GET` | `/api/v1/rag/users/{user_id}/loyalty/` | Loyalty tier, miles, benefits |
| 6 | `GET` | `/api/v1/rag/flights/search/` | Search available flights |
