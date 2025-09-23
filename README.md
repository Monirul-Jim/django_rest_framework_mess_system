# Mess Management System - Django REST API

A comprehensive mess management system API built with Django REST Framework that handles user authentication, mess creation, member management, meal tracking, and monthly calculations.

## Features

- **User Authentication**: JWT-based authentication with refresh tokens
- **Mess Management**: Create and manage multiple messes
- **Member Management**: Add members by phone number with role-based access
- **Meal Tracking**: Track daily meals (0-3 meals per day per member)
- **Monthly Calculations**: Automatic calculation of bazaar costs, extra costs, and member-wise bills
- **Role-based Access**: Owner, Manager, and Member roles with appropriate permissions

## Setup Instructions

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Database Setup
```bash
python manage.py makemigrations accounts
python manage.py makemigrations mess_management
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/auth/signup/` - User registration
- `POST /api/auth/signin/` - User login
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/logout/` - Logout

### Mess Management
- `GET /api/mess/` - List user's messes
- `POST /api/mess/` - Create new mess
- `GET /api/mess/{id}/` - Get mess details
- `POST /api/mess/{id}/add_member/` - Add member by phone
- `POST /api/mess/{id}/add_manager/` - Add manager (owner only)

### Meal Tracking
- `POST /api/mess/{id}/meals/` - Add meal entry
- `GET /api/mess/{id}/meals/{month}/` - Get meals for month

### Monthly Calculations
- `POST /api/mess/{id}/calculate/{month}/` - Calculate monthly costs
- `GET /api/mess/{id}/calculation/{month}/` - Get monthly calculation

## Frontend Integration

Update your Redux API base URL to point to your Django server:

```typescript
// store/api.ts
const baseQuery = fetchBaseQuery({
  baseUrl: 'http://localhost:8000/api', // Change this to your Django server URL
  // ... rest of configuration
})
```

## Database Models

### User (Custom User Model)
- Extended Django's AbstractUser
- Added phone field for member identification
- Used for authentication and member management

### Mess
- name, description
- owner (ForeignKey to User)
- members (ManyToMany to User)
- managers (ManyToMany to User)

### Meal
- mess, member, date, meal_count
- added_by (tracking who added the meal)
- Unique constraint on (mess, member, date)

### MonthlyCalculation
- mess, month, costs, totals
- calculated_by (tracking who performed calculation)

### MemberMealSummary
- Links calculation to member with totals
- Used for member-wise cost breakdown

## Role-based Permissions

### Owner
- Create mess (automatic owner)
- Add/remove managers
- All manager permissions

### Manager
- Add members by phone number
- Track daily meals
- Calculate monthly costs
- View all mess data

### Member
- View mess details
- View meal history
- View monthly calculations

## Development Notes

- Uses JWT tokens with refresh token stored in HTTP-only cookies
- Phone numbers are used for member identification
- Supports Bangladesh currency (৳) formatting
- Monthly calculations include bazaar costs and extra expenses (khoroc)
- All API responses follow consistent JSON format

## Production Deployment

1. Set DEBUG=False in settings
2. Configure proper DATABASE_URL
3. Set up static files serving
4. Configure CORS for your frontend domain
5. Use environment variables for sensitive data