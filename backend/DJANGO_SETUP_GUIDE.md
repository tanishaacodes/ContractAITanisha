# Django Backend - ContractAI

This is the Python Django migration of the Node.js/Express backend for ContractAI.

## Quick Start

### 1. Environment Setup

```bash
cd django_backend
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py initialize_roles
```

### 4. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current authenticated user

### Contracts
- `POST /api/contracts/upload` - Upload and process a contract file
- `GET /api/contracts/list` - Get list of user's contracts
- `GET /api/contracts/<contract_id>` - Get specific contract details
- `DELETE /api/contracts/<filename>` - Delete a contract file

### Clause Extraction
- `POST /api/contracts/<contract_id>/extract-clauses` - Extract clauses from contract
- `GET /api/contracts/<contract_id>/clauses` - Get extracted clauses for a contract

### Admin Endpoints (requires Admin role)
- `GET /api/admin/users` - List all users
- `POST /api/admin/users/<user_id>/role` - Update user role
- `POST /api/admin/users/<user_id>/status` - Toggle user active status
- `GET /api/admin/roles` - List all available roles

## Differences from Node.js Backend

### Models/Database
- **Role Model**: Same structure, supports Admin, Legal Reviewer, Proc Reviewer, Viewer roles
- **User Model**: Same structure with bcrypt password hashing
- **Contract Model**: Same structure with UUID primary key
- **Clause Model**: Same structure with JSON fields for text_spans and context_sentences

### Authentication
- Uses **JWT (JSON Web Tokens)** instead of Express session tokens
- Token format: `Authorization: Bearer <token>`
- Tokens expire after 24 hours (configurable)

### File Upload & Processing
- Uses Django's file upload system instead of Multer
- OCR powered by **Tesseract.js equivalent in Python (pytesseract)**
- PDF processing uses **PyPDF2** and **pdf2image**
- DOCX processing uses **python-docx**
- Image processing uses **Pillow**

### Configuration
- Settings managed in `contractai/settings.py`
- Environment variables can be loaded from `.env` file (use `.env.example` as template)
- CORS configured for `http://localhost:3000` and `http://localhost:3001`

## Database

Currently using **SQLite** for development. To switch to MySQL:

1. Install MySQL client:
```bash
pip install mysqlclient
```

2. Update `contractai/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'contractai',
        'USER': 'root',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

## React Frontend Integration

Update your React API client to point to the Django backend:

```javascript
const API_BASE_URL = 'http://localhost:8000/api';

// Login example
const response = await fetch(`${API_BASE_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const data = await response.json();
localStorage.setItem('token', data.token);

// Authenticated request example
const contractResponse = await fetch(`${API_BASE_URL}/contracts/list`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```

## Admin Panel

Access Django admin at `http://localhost:8000/admin/` with superuser credentials.

You can manage:
- Users and their roles
- Contracts and their data
- Extracted clauses
- Roles and permissions

## Testing Endpoints

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123","firstName":"John","lastName":"Doe"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'
```

### Upload Contract
```bash
curl -X POST http://localhost:8000/api/contracts/upload \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@path/to/contract.pdf"
```

## Troubleshooting

### OCR Issues
- Ensure Tesseract is installed on your system
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`

### PDF Processing Issues
- Some PDFs might be image-based and require OCR
- OCR fallback is automatic if PDF text extraction fails

### Database Issues
- Delete `db.sqlite3` and run migrations again if you have schema issues
- For MySQL, ensure MySQL server is running and database is created

## Project Structure

```
django_backend/
├── contractai/          # Django project settings
│   ├── settings.py      # Configuration
│   ├── urls.py          # URL routing
│   └── wsgi.py          # WSGI application
├── core/                # Core models and auth
│   ├── models.py        # Database models
│   ├── authentication.py # JWT authentication
│   ├── serializers.py   # DRF serializers
│   ├── admin.py         # Django admin configuration
│   └── migrations/      # Database migrations
├── api/                 # API views and utilities
│   ├── views.py         # API endpoints
│   ├── urls.py          # API URL routing
│   ├── utils.py         # File processing utilities
│   └── serializers.py   # API serializers
├── admin_app/           # Admin-only endpoints
│   ├── views.py         # Admin views
│   └── urls.py          # Admin URL routing
├── uploads/             # User uploaded files
├── manage.py            # Django management script
└── requirements.txt     # Python dependencies
```

## Notes

- This is a complete port of the Node.js backend to Django
- All endpoints maintain API compatibility with the original backend
- The React frontend should work without modification (except API_BASE_URL update)
- JWT tokens are used instead of session cookies for stateless authentication
- All file processing (OCR, PDF extraction, DOCX parsing) has been ported to Python equivalents
