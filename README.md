BankEase – Backend
Project: BankEase – NextGen Net Banking Application
Project Code: P18
Repository: Bankease-Backend

This repository contains the Django backend for BankEase. It exposes REST API services used by the separate HTML, CSS and JavaScript frontend. The backend handles application logic, authentication, server-side validation and communication with the PostgreSQL database hosted on Supabase.
Academic demo notice: This is an educational banking application. Its financial workflows are simulated and are not connected to real banking rails. Do not use it for real-money transactions or real customer information.

Technology stack
Component	Technology
Language	Python 3.12
Web framework	Django 6.1.3
API layer	Django REST Framework 3.18.3
Authentication	Simple JWT (djangorestframework-simplejwt)
Database	PostgreSQL on Supabase
PostgreSQL driver	Psycopg 3
Environment configuration	python-decouple, python-dotenv
Production application server	Gunicorn
Static-file handling	WhiteNoise
Cross-origin requests	django-cors-headers
Hosting	Render


Pinned package versions are maintained in requirements.txt. Refer to that file when installing dependencies.
Responsibilities of the backend
- Receive requests from the frontend through REST API endpoints.
- Register and authenticate customer users.
- Issue and validate JWTs for protected API requests.
- Apply role-based access rules for customer and bank-officer operations.
- Validate request data on the server before performing operations.
- Read and update application data in Supabase PostgreSQL.
- Return JSON responses and suitable HTTP status codes to the frontend.
Application modules
The application is organised under the apps/ package, with Django project configuration under config/. The project covers the following functional areas:
- Authentication and user/account management.
- Customer bank accounts and beneficiaries.
- Demo fund transfers and transaction records.
- Utility bill payments.
- Loan products, applications and repayment-related operations.
- Investment products and investment records.
- Notifications and customer-support workflows.
- Bank-officer operations and review of pending requests.
The exact API paths and model names are defined by the code in apps/ and the URL configuration. Use those files as the authoritative API reference rather than assuming endpoint names from this overview.
Repository structure
Bankease-Backend/
├── apps/                 # Django application modules
├── config/               # Django project settings and URL/WSGI configuration
├── .env.example          # Example environment-variable template
├── .gitignore
├── Dockerfile            # Container build instructions
├── Procfile              # Gunicorn start command
├── build.sh              # Render build steps
├── manage.py             # Django management entry point
└── requirements.txt      # Pinned Python dependencies
Requirements
- Python 3.12.
- pip.
- Git.
- Access to a PostgreSQL database. The hosted project uses Supabase PostgreSQL.
- Environment variables configured using the template in .env.example.
Local setup (Windows PowerShell)
Run these commands from the backend repository directory:
1. Create and activate a virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
If PowerShell blocks script activation, use the activation method permitted by your local machine's execution policy, or run the project from Command Prompt with .venv\Scripts\activate.bat.
2. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
3. Configure environment variables
Create a local .env file from the example:
Copy-Item .env.example .env
Open .env and enter the database connection details and Django settings required by the project. Use the variable names already present in .env.example and the Render configuration. For Supabase PostgreSQL, use the correct host, database, username, password and port provided by your Supabase project, and keep SSL mode enabled as required by the deployment configuration.

Never commit .env or share its contents. The .env.example file should contain variable names and safe placeholders only.
4. Apply database migrations
python manage.py migrate
5. Check the Django configuration
python manage.py check
6. Start the development server
python manage.py runserver 127.0.0.1:8000
The local backend will be available at:
http://127.0.0.1:8000/
The frontend is expected to call the API under the project's /api/v1/ prefix. Start the frontend separately by following its README.
Local setup (macOS / Linux)
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your own local/Supabase configuration.
python manage.py migrate
python manage.py check
python manage.py runserver 127.0.0.1:8000
Authentication and access control
The project uses JWT-based authentication through Simple JWT. In a typical flow:
1. The frontend sends login credentials to the backend.
2. The backend validates the credentials.
3. On successful authentication, the backend returns the configured token response.
4. The frontend sends the access token with subsequent protected API requests.
5. The backend verifies the token and checks the user's permissions before processing the request.
Customer and bank-officer access should be controlled on the server. Hiding a page or button in JavaScript is not sufficient authorization. Officer accounts should be provisioned through a controlled administrative/setup process; public customer registration should not grant officer privileges. A Django superuser and an application-level bank officer are not automatically the same role.
Demo fund-transfer workflow
Fund transfers in this academic project are simulated database operations. The backend should validate the sender, receiver and amount, check the sender's available balance, perform the debit/credit updates consistently, and record the transaction. No real money moves between bank accounts. Real-world payment or interbank transfer processing requires authorized banking/payment infrastructure and security controls that are outside this project's scope.
Deployment on Render
The repository includes deployment support files:
- build.sh installs dependencies, runs collectstatic and applies migrations.
- Procfile starts Gunicorn with config.wsgi:application.
- Dockerfile provides a container build definition.
- render.yaml in the separate Deployment repository describes the Render web service and environment-variable configuration.
The Render service is configured to use Python 3.12, execute ./build.sh and start with:
gunicorn config.wsgi:application
Set the required environment variables in Render's service settings. The deployment blueprint lists the database connection variables, DJANGO_SECRET_KEY, DEBUG, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS. Supply actual values through the hosting dashboard; do not write secrets into source code.
Useful Django commands
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
createsuperuser creates a Django administrative account. It should not be assumed to create an application-level Bank Officer unless the project's role model and provisioning logic explicitly do so.
Security and project limitations
- Keep DEBUG=False in deployed environments.
- Use a strong, private Django secret key.
- Keep database credentials in environment variables, never in Git.
- Configure ALLOWED_HOSTS, CORS and CSRF trusted origins for the actual deployed domains.
- Enforce authentication, authorization and validation on the backend.
- Use HTTPS in deployed environments.
- Avoid logging passwords, tokens or private financial information.
- This project has not been presented as a production-certified banking system; additional security review, testing, monitoring, KYC and regulated integrations would be required for real-world use.
Related repositories
- Frontend – HTML, CSS and JavaScript interface
- Deployment – Docker Compose and Render configuration
