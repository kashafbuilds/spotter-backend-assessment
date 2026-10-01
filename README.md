# Spotter Backend Assessment

A Django REST Framework backend for the Spotter Backend Engineer assessment.

The API accepts start and finish coordinates within the USA, calculates a driving route, identifies cost-effective fueling locations along the route, respects a vehicle maximum range of 500 miles, and estimates total fuel cost using a fuel economy of 10 miles per gallon.

## Tech Stack

* Python 3
* Django 5.2
* Django REST Framework
* SQLite
* OpenRouteService
* Requests
* python-decouple

## Key Features

* Fuel station data imported from the provided CSV
* 8,151 fuel station records
* Fuel station filtering by state and city
* Fuel price filtering
* Fuel price sorting
* Nearby fuel station search
* Driving route calculation
* Fuel-stop optimization for routes longer than 500 miles
* 500-mile maximum vehicle range
* 10 MPG fuel economy assumption
* Total estimated fuel consumption and cost
* Automated API tests
* Environment-based API key configuration

---

## Project Setup

### 1. Clone the repository

```bash
git clone https://github.com/kashafbuilds/spotter-backend-assessment.git
cd spotter-backend-assessment
```

### 2. Create and activate the virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
OPENROUTESERVICE_API_KEY=your_api_key_here
```

Do not commit the `.env` file to GitHub.

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Import fuel station data

The provided fuel-price dataset is located at:

```text
data/fuel-prices.csv
```

Import the data with:

```bash
python manage.py import_fuel_data
```

### 7. Start the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

---

# API Endpoints

## API Root

```http
GET /api/
```

## Fuel Stations

```http
GET /api/fuel-stations/
GET /api/fuel-stations/<id>/
```

## Filter by State

```http
GET /api/fuel-stations/?state=OK
```

## Filter by City

```http
GET /api/fuel-stations/?city=Tulsa
```

## Filter by Price

Minimum price:

```http
GET /api/fuel-stations/?min_price=3.50
```

Maximum price:

```http
GET /api/fuel-stations/?max_price=3.00
```

Price range:

```http
GET /api/fuel-stations/?min_price=3.00&max_price=3.50
```

## Sort by Retail Price

Lowest to highest:

```http
GET /api/fuel-stations/?ordering=retail_price
```

Highest to lowest:

```http
GET /api/fuel-stations/?ordering=-retail_price
```

---

# Nearby Fuel Stations

Endpoint:

```http
GET /api/fuel-stations/nearby/
```

Required parameters:

* `lat`
* `lon`

Optional parameter:

* `radius_km` — search radius in kilometers; default is 50 km

Example:

```http
GET /api/fuel-stations/nearby/?lat=35.4676&lon=-97.5164&radius_km=50
```

The endpoint calculates the geographic distance between the requested coordinates and available fuel stations using the Haversine formula.

Results are returned sorted by distance.

### Validation

Missing coordinates:

```http
GET /api/fuel-stations/nearby/
```

Returns HTTP 400.

Invalid coordinates:

```http
GET /api/fuel-stations/nearby/?lat=abc&lon=-97.5164&radius_km=50
```

Returns HTTP 400.

Invalid radius:

```http
GET /api/fuel-stations/nearby/?lat=35.4676&lon=-97.5164&radius_km=0
```

Returns HTTP 400.

---

# Route and Fuel Optimization

## Endpoint

```http
GET /api/fuel-stations/route/
```

Required parameters:

* `start_lat`
* `start_lon`
* `finish_lat`
* `finish_lon`

Example:

```http
GET /api/fuel-stations/route/?start_lat=40.7128&start_lon=-74.0060&finish_lat=41.8781&finish_lon=-87.6298
```

This example represents a route from New York City to Chicago.

## Route Calculation

The route is calculated using OpenRouteService's driving directions API.

The API returns:

* Route distance in miles
* Estimated duration in minutes
* Route geometry as GeoJSON
* Fuel stops
* Fuel price at selected stations
* Distance between fuel stops
* Estimated gallons required
* Fuel cost
* Total fuel consumption
* Total estimated fuel cost

## Vehicle Assumptions

The assessment specifies:

```text
Maximum vehicle range: 500 miles
Fuel economy: 10 miles per gallon
```

These values are represented in the API response:

```json
{
    "max_range_miles": 500.0,
    "fuel_economy_mpg": 10.0
}
```

## Fuel Optimization

For longer routes, the API builds candidate fueling locations near the calculated route.

Candidate stations are limited to a route corridor of approximately 50 miles.

A dynamic-programming approach is used to select a feasible sequence of fuel stops while respecting the vehicle's 500-mile maximum range.

For each possible leg:

```text
gallons required = leg distance / 10 MPG
```

and:

```text
fuel cost = gallons required × fuel price
```

The selected plan must ensure that every individual driving leg remains within the 500-mile vehicle range.

The response also reports the final leg to the destination.

---

# Example Route Response

A successful route response contains the following main sections:

```json
{
    "route": {
        "distance_miles": 796.7,
        "duration_minutes": 831.61,
        "geometry": {}
    },
    "vehicle": {
        "max_range_miles": 500.0,
        "fuel_economy_mpg": 10.0
    },
    "fuel_plan": {
        "stops": [],
        "total_fuel_gallons": 79.67,
        "total_fuel_cost": 244.24,
        "stations_considered": 71,
        "final_leg_miles": 319.64
    }
}
```

The actual response includes the complete GeoJSON route geometry and selected fuel station details.

---

# Pagination

Fuel station results use page-number pagination.

Default page size:

```text
20 results per page
```

Example:

```http
GET /api/fuel-stations/?page=2
```

---

# Data

The provided fuel dataset contains:

```text
8,151 fuel station records
```

The CSV contains:

* OPIS Truckstop ID
* Truckstop Name
* Address
* City
* State
* Rack ID
* Retail Price

The original CSV does not contain latitude and longitude fields.

Latitude and longitude fields were therefore added to the database model to support geographic and route-based functionality.

---

# Geocoding

Because the supplied CSV does not include coordinates, fuel station coordinates were generated using OpenRouteService geocoding based on station city/state information.

This is an approximation rather than exact address-level geocoding.

Only stations with available coordinates can participate in geographic and route-corridor calculations.

The OpenRouteService API key is loaded from `.env` using `python-decouple`.

---

# Routing API Usage

The project uses OpenRouteService for driving route calculation.

The route endpoint is designed to make a single routing request for a start and finish location and then perform fuel-station selection locally.

This helps minimize external routing API calls.

---

# Testing

Run Django system checks:

```bash
python manage.py check
```

Expected result:

```text
System check identified no issues (0 silenced).
```

Run automated tests:

```bash
python manage.py test
```

Current test suite:

```text
Found 6 test(s).
......
Ran 6 tests
OK
```

The automated tests cover:

* Fuel station listing
* State filtering
* City filtering
* Nearby endpoint validation
* Nearby station search
* Route endpoint required-parameter validation

Additional manual testing was performed for:

* Pagination
* Minimum price filtering
* Maximum price filtering
* Price range filtering
* Ascending price sorting
* Descending price sorting
* Nearby station search
* Invalid coordinates
* Invalid radius
* Long-distance route calculation
* Fuel-stop selection
* 500-mile range constraints

---

# Known Limitations and Assumptions

### 1. Coordinate accuracy

The provided fuel-price CSV does not contain latitude/longitude data.

Station coordinates are therefore based on city/state geocoding and should be treated as approximate.

### 2. Route corridor

Candidate stations are considered when they are approximately within 50 miles of the calculated route.

### 3. Input format

The route endpoint currently accepts latitude and longitude coordinates rather than text addresses.

This avoids an additional address-geocoding request for the user's start and finish locations.

### 4. Fuel consumption

Fuel consumption is estimated using the fixed assessment assumption of:

```text
10 miles per gallon
```

Therefore:

```text
total gallons = route miles / 10
```

### 5. Fuel pricing model

Fuel cost is estimated using the retail price supplied by the provided dataset.

The optimization focuses on selecting feasible, cost-effective fueling locations under the 500-mile vehicle range constraint.

### 6. Geographic distance approximation

The route-corridor calculation uses geographic distance approximations rather than exact road-network distance from every station to every route segment.

---

# Security

Sensitive API keys are stored in `.env` and must not be committed to version control.

The `.env` file is included in `.gitignore`.

Never place the OpenRouteService API key directly in source code or the README.

---

# GitHub

Repository:

```text
https://github.com/kashafbuilds/spotter-backend-assessment
```

---

# Assessment Deliverables

The project includes:

* Django REST API
* Fuel station dataset import
* Route calculation
* Fuel-stop optimization
* Fuel cost estimation
* Automated tests
* Environment-based API configuration
* GitHub source code

A short Loom demonstration should show the route endpoint being called through Postman or another API client, followed by a brief overview of the implementation.
