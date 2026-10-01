# Spotter Backend Assessment

A Django REST Framework backend for managing fuel station data, filtering and sorting fuel prices, and finding nearby fuel stations using geographic coordinates.

## Tech Stack

* Python 3
* Django
* Django REST Framework
* SQLite
* OpenRouteService
* python-decouple

## Project Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Spotter-Backend-Assessment
```

### 2. Create and activate virtual environment

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

The fuel station CSV is located at:

```text
data/fuel-prices.csv
```

Run:

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

## API Endpoints

### API Root

```http
GET /api/
```

### Products

```http
GET /api/products/
GET /api/products/<id>/
POST /api/products/
PUT /api/products/<id>/
PATCH /api/products/<id>/
DELETE /api/products/<id>/
```

### Fuel Stations

```http
GET /api/fuel-stations/
GET /api/fuel-stations/<id>/
```

### Filter by State

```http
GET /api/fuel-stations/?state=OK
```

### Filter by City

```http
GET /api/fuel-stations/?city=Tulsa
```

### Filter by Price

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

### Sort by Retail Price

Lowest to highest:

```http
GET /api/fuel-stations/?ordering=retail_price
```

Highest to lowest:

```http
GET /api/fuel-stations/?ordering=-retail_price
```

### Nearby Fuel Stations

```http
GET /api/fuel-stations/nearby/?latitude=35.4676&longitude=-97.5164&radius=50
```

Parameters:

* `latitude` — required
* `longitude` — required
* `radius` — optional, in kilometers; default is 10 km

The nearby endpoint uses the Haversine formula to calculate geographic distance.

## Pagination

Fuel station results use page-number pagination.

Default page size:

```text
20 results per page
```

Example:

```http
GET /api/fuel-stations/?page=2
```

## Nearby API Validation

Missing coordinates:

```http
GET /api/fuel-stations/nearby/
```

Returns:

```json
{
    "error": "latitude and longitude are required."
}
```

Invalid coordinates:

```http
GET /api/fuel-stations/nearby/?latitude=abc&longitude=-97.5164&radius=50
```

Returns:

```json
{
    "error": "latitude, longitude and radius must be numbers."
}
```

Invalid radius:

```http
GET /api/fuel-stations/nearby/?latitude=35.4676&longitude=-97.5164&radius=0
```

Returns:

```json
{
    "error": "radius must be greater than 0."
}
```

## Data

The provided fuel dataset contains 8,151 fuel station records.

The CSV contains:

* OPIS Truckstop ID
* Truckstop Name
* Address
* City
* State
* Rack ID
* Retail Price

Latitude and longitude fields are stored in the database for geographic search functionality.

## Geocoding

OpenRouteService is used to geocode fuel station locations.

Because the provided CSV does not contain latitude and longitude values, geographic coordinates are generated from city/state locations.

The OpenRouteService API key is loaded securely from the `.env` file using `python-decouple`.

## Testing

Run Django's system checks:

```bash
python manage.py check
```

Expected result:

```text
System check identified no issues (0 silenced).
```

The API was manually tested for:

* Fuel station listing
* Pagination
* State filtering
* City filtering
* Minimum price filtering
* Maximum price filtering
* Price range filtering
* Ascending price sorting
* Descending price sorting
* Nearby station search
* Missing parameter validation
* Invalid parameter validation
* Radius validation

## Security

Sensitive API keys are stored in `.env` and should not be committed to version control.

The `.env` file should be included in `.gitignore`.

## License

This project was created as part of a backend coding assessment.
