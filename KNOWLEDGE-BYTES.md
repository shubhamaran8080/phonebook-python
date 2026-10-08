# Phonebook Python — Knowledge Bytes

> Notes explaining the Phonebook project step by step

---

### Byte 1: Overall Project Architecture

**Builds on:** None — starting point

**In plain terms:**

This Phonebook project is a full-stack web application. The user manages contacts through the frontend, the frontend sends requests to the FastAPI backend, the backend communicates with the PostgreSQL database, and the result is returned to the frontend. A login system protects the contact data: the frontend signs in once, receives a JWT, and sends it with every request.

**The architecture:**

```text
User
  ↓
Vue.js Frontend (JWT stored in localStorage)
  ↓
FastAPI Backend (JWT verified on protected routes)
  ↓
PostgreSQL Database
  ↓
FastAPI Response
  ↓
Vue.js Frontend
```

---

### Byte 2: Project Structure

**Builds on:** Byte 1

**In plain terms:**

The project is divided into separate frontend, backend, database, testing, and Docker-related files. Each folder and file has a specific responsibility, which keeps the application organized and easier to maintain.

**The project structure:**

```text
PhonebookPython/
│
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + API endpoints
│   │   ├── database.py      # engine, session, Base
│   │   ├── models.py        # Contact and User models
│   │   ├── schemas.py       # Pydantic validation schemas
│   │   ├── crud.py          # database operations
│   │   └── auth.py          # bcrypt hashing + JWT helpers
│   │
│   ├── tests/
│   │   ├── conftest.py      # test fixtures
│   │   ├── test_contacts.py
│   │   └── test_auth.py
│   │
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed.py              # demo user + dummy contact generator
│
├── frontend/
│   ├── src/
│   │   ├── main.js          # app entry, 401 → login wiring
│   │   ├── App.vue          # sidebar / hamburger app shell
│   │   ├── router.js        # routes + auth guard
│   │   ├── api.js           # axios wrapper + interceptors
│   │   ├── auth.js          # auth state (token in localStorage)
│   │   ├── style.css        # design system styles
│   │   └── views/
│   │       ├── DashboardView.vue
│   │       ├── ContactList.vue
│   │       ├── ContactDetail.vue
│   │       ├── CreateContact.vue
│   │       ├── LoginView.vue
│   │       └── ProfileView.vue
│   │
│   ├── Dockerfile
│   ├── nginx.conf           # serves the app, proxies /api → backend
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

### Byte 3: FastAPI Application Entry Point — `main.py`

**Builds on:** Byte 2

**In plain terms:**

`backend/app/main.py` is the main entry point of the FastAPI backend. It creates the FastAPI application and defines the API endpoints that the frontend can call: a health check, contact CRUD, authentication, and dashboard statistics.

**The code:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for the containerized setup; a migration tool
    # such as Alembic can replace this in production).
    models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Phonebook API", version="1.0.0", lifespan=lifespan)
```

The app also enables CORS middleware so the separately served frontend can call the API during development.

---

### Byte 4: API Data Validation — `schemas.py`

**Builds on:** Byte 3

**In plain terms:**

`backend/app/schemas.py` defines the structure and validation rules for data entering and leaving the API. It uses Pydantic models to make sure that contact data has the expected format before the backend processes it. It also defines the login payload, the user response, and the dashboard statistics response.

**The code:**

```python
# E.164 style: a leading '+', a country code starting 1-9, then up to 14 digits.
PHONE_NUMBER_PATTERN = r"^\+[1-9]\d{1,14}$"


class ContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone_number: str = Field(..., pattern=PHONE_NUMBER_PATTERN)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
```

Other models in the same file: `ContactCreate`, `ContactUpdate` (a partial update — only fields that are explicitly provided are changed), `ContactResponse` (adds `id` and `created_at`), `LoginRequest`, `UserResponse` (never includes the password hash), and `StatsResponse`.

---

### Byte 5: Database Models — `models.py`

**Builds on:** Byte 4

**In plain terms:**

`backend/app/models.py` defines the SQLAlchemy database models. The `Contact` class represents a row in the PostgreSQL `contacts` table, and the `User` class represents a row in the `users` table used for authentication.

**The code:**

```python
class Contact(Base):
    """A single phonebook entry."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

The `User` model stores `username` (unique, indexed), an optional unique `email`, the bcrypt `hashed_password`, and `created_at`.

---

### Byte 6: Database Connection — `database.py`

**Builds on:** Byte 5

**In plain terms:**

`backend/app/database.py` is responsible for connecting the FastAPI backend to PostgreSQL. It creates the database engine and provides a database session that can be used by the API operations.

**The code:**

```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://phonebook:phonebook@db:5432/phonebook",
)

engine = create_engine(DATABASE_URL)
```

The default URL points at the Docker Compose service name `db`, which is how the backend reaches PostgreSQL inside the Docker network.

---

### Byte 7: Database Operations — `crud.py`

**Builds on:** Byte 6

**In plain terms:**

`backend/app/crud.py` contains the functions that perform database operations for contacts. Instead of putting database queries directly inside the API routes, the project keeps these operations in a separate CRUD layer. Besides contact CRUD, it provides the search filtering, counting, and statistics queries used by the list view and the dashboard.

**The code:**

The CRUD layer works with a SQLAlchemy database session and the `Contact` model.

A typical create operation follows this pattern:

```python
db_contact = models.Contact(**contact.model_dump())
db.add(db_contact)
db.commit()
db.refresh(db_contact)
return db_contact
```

Search is applied with SQL `ILIKE` on the name or phone number, and pagination uses `offset()` and `limit()`:

```python
def get_contacts(db: Session, *, skip: int = 0, limit: int = 100, search=None):
    return (
        _apply_search(db.query(models.Contact), search)
        .order_by(models.Contact.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
```

---

### Byte 8: Creating a Contact Through the API

**Builds on:** Byte 7

**In plain terms:**

When the frontend wants to create a new contact, it sends the contact information (with the JWT in the Authorization header) to the FastAPI backend. The backend verifies the token, validates the data using the schema, and then uses the CRUD layer to save the contact in PostgreSQL.

**The flow:**

```text
Vue Frontend
     ↓
POST API Request (Bearer token)
     ↓
FastAPI Route (JWT check)
     ↓
ContactCreate Schema
     ↓
CRUD Create Operation
     ↓
PostgreSQL
     ↓
Response
     ↓
Vue Frontend
```

A successful create returns HTTP 201 with the created contact; a duplicate phone number or email returns HTTP 409.

---

### Byte 9: Reading Contacts from the API

**Builds on:** Byte 8

**In plain terms:**

The application also needs to retrieve contacts from PostgreSQL and display them in the frontend. The frontend sends a GET request to the FastAPI backend, and the backend retrieves the required contacts through the CRUD layer.

**The flow:**

```text
Vue Frontend
     ↓
GET API Request (Bearer token)
     ↓
FastAPI Route (JWT check)
     ↓
CRUD Read Operation
     ↓
PostgreSQL
     ↓
Contact Data
     ↓
FastAPI Response
     ↓
Vue Frontend
```

The list endpoint supports `page`, `page_size` (1–100), and a `q` search term. Because the response body is a plain list, the pagination metadata is returned in headers: `X-Total-Count`, `X-Page`, and `X-Page-Size`.

---

### Byte 10: Updating a Contact

**Builds on:** Byte 9

**In plain terms:**

The Phonebook application allows an existing contact to be edited. The frontend sends the contact ID and the updated information to the FastAPI backend, which validates the data and updates the corresponding record in PostgreSQL.

**The flow:**

```text
Vue Frontend
     ↓
PUT API Request (Bearer token)
     ↓
FastAPI Route (JWT check)
     ↓
ContactUpdate Schema
     ↓
CRUD Update Operation
     ↓
PostgreSQL
     ↓
Updated Contact
     ↓
FastAPI Response
     ↓
Vue Frontend
```

Only the fields present in the request body are changed (`model_dump(exclude_unset=True)`), so a partial update does not wipe the other fields.

---

### Byte 11: Deleting a Contact

**Builds on:** Byte 10

**In plain terms:**

The Phonebook application also allows the user to remove an existing contact. The frontend sends a delete request for a specific contact, and the backend removes that record from PostgreSQL through the CRUD layer.

**The flow:**

```text
Vue Frontend
     ↓
DELETE API Request (Bearer token)
     ↓
FastAPI Route (JWT check)
     ↓
CRUD Delete Operation
     ↓
PostgreSQL
     ↓
Response
     ↓
Vue Frontend
```

A successful delete returns HTTP 204 with no body.

---

### Byte 12: Frontend Entry Point — `main.js`

**Builds on:** Byte 11

**In plain terms:**

`frontend/src/main.js` is the entry point of the Vue.js frontend. It creates the Vue application, connects the router, loads the global stylesheet, and registers a handler that sends the user back to the login screen whenever the backend answers a request with 401 (for example, an expired token).

**The code:**

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { onUnauthorized } from './api'
import './style.css'

// When the backend rejects a request with 401 (expired/invalid
// token), send the user back to the login screen.
onUnauthorized(() => {
  if (router.currentRoute.value.name !== 'login') {
    router.push({ name: 'login' })
  }
})

createApp(App).use(router).mount('#app')
```

---

### Byte 13: API Communication — `api.js`

**Builds on:** Byte 12

**In plain terms:**

`frontend/src/api.js` is responsible for communicating with the FastAPI backend. Instead of writing HTTP request code separately inside every Vue component, the frontend keeps the API-related logic in one place. It creates an axios instance whose base URL is `/api` — inside Docker, nginx proxies `/api` to the backend.

**The code:**

```javascript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api'
})
```

The file also exports the API methods (`login`, `logout`, `getMe`, `getStats`, `listContacts`, `getContact`, `createContact`, `updateContact`, `deleteContact`) and an `extractError` helper that turns API errors into readable messages. The request/response interceptors that attach the token are covered in Byte 32.

---

### Byte 14: Vue Application Root — `App.vue`

**Builds on:** Byte 13

**In plain terms:**

`frontend/src/App.vue` is the main/root Vue component of the application. It provides the common structure of the frontend: a sidebar navigation on desktop, a hamburger slide-over menu on mobile, a top bar, and the `<router-view>` where the current page is displayed. The sidebar and top bar are only rendered when a user is signed in.

**The code:**

```vue
<aside class="sidebar" :class="{ open: sidebarOpen }" v-if="auth.user">
  <!-- brand, navigation links, user chip, logout button -->
</aside>
<div class="sidebar-backdrop" v-if="sidebarOpen && auth.user" @click="sidebarOpen = false"></div>

<div class="main-wrapper">
  <header class="topbar" v-if="auth.user">
    <button class="hamburger" @click="sidebarOpen = true" aria-label="Open menu">...</button>
    <span class="topbar-title">{{ pageTitle }}</span>
  </header>
  <main class="main-content">
    <router-view />
  </main>
</div>
```

The navigation menu itself is covered in Byte 37.

---

### Byte 15: Frontend Routing — `router.js`

**Builds on:** Byte 14

**In plain terms:**

`frontend/src/router.js` defines the routes of the Vue application. It connects browser URLs to the Vue components that should be displayed. Every protected route carries `requiresAuth: true` metadata, and a navigation guard redirects signed-out users to the login page.

**The code:**

```javascript
const routes = [
  { path: '/', name: 'dashboard', component: Dashboard, meta: { requiresAuth: true, title: 'Dashboard' } },
  { path: '/contacts', name: 'contacts', component: ContactList, meta: { requiresAuth: true, title: 'Contacts' } },
  { path: '/contacts/new', name: 'create-contact', component: CreateContact, meta: { requiresAuth: true, title: 'Add Contact' } },
  { path: '/contacts/:id', name: 'contact-detail', component: ContactDetail, props: true, meta: { requiresAuth: true, title: 'Contact Details' } },
  { path: '/profile', name: 'profile', component: Profile, meta: { requiresAuth: true, title: 'Account' } },
  { path: '/login', name: 'login', component: Login, meta: { title: 'Sign in' } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]
```

The route titles feed the top bar's page title. The navigation guard is covered in Byte 33.

---

### Byte 16: Contact List View — `ContactList.vue`

**Builds on:** Byte 15

**In plain terms:**

`frontend/src/views/ContactList.vue` is responsible for displaying the contacts to the user. It is the main view where the stored phonebook entries can be viewed and where actions such as searching, pagination, and navigation to contact details are handled.

**The code:**

```vue
<template>
  <!-- Contact list UI -->
</template>
```

The view fetches contacts through `api.listContacts({ page, pageSize, search })`, reads the total from the `X-Total-Count` response header, and provides a search box, a page-size selector (10 / 25 / 50 per page), skeleton rows while loading, empty and error states, pagination buttons, and an Edit link and Delete button per contact.

---

### Byte 17: Contact Creation, Detail, Login, and Account Views

**Builds on:** Byte 16

**In plain terms:**

The frontend keeps separate views for each user action: creating a contact, viewing/editing a contact, signing in, the dashboard, and the account page. This keeps different user actions separated into focused Vue components.

**The files:**

```text
frontend/src/views/
├── DashboardView.vue      # statistics + recent contacts
├── ContactList.vue        # search, pagination, list
├── ContactDetail.vue      # detail view + edit form
├── CreateContact.vue      # add-contact form
├── LoginView.vue          # sign-in form
└── ProfileView.vue        # signed-in user info + sign out
```

The detail/edit view is covered in Byte 38, the login screen in Byte 34, and the dashboard in Byte 36.

---

### Byte 18: Docker Compose — Running the Complete Application

**Builds on:** Byte 17

**In plain terms:**

`docker-compose.yml` defines the services required to run the Phonebook application together. Instead of manually installing and starting PostgreSQL, the FastAPI backend, and the frontend separately, Docker Compose manages them as connected services. All three services use `restart: unless-stopped`, so they come back automatically after a Docker engine restart.

**The structure:**

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-phonebook}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-phonebook}
      POSTGRES_DB: ${POSTGRES_DB:-phonebook}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-phonebook} -d ${POSTGRES_DB:-phonebook}"]

  backend:
    build: ./backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+psycopg2://...@db:5432/phonebook
      SECRET_KEY: ${SECRET_KEY:-}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build: ./frontend
    restart: unless-stopped
    ports:
      - "8080:80"
    depends_on:
      - backend
```

The backend waits for the `pg_isready` healthcheck before starting, and the `SECRET_KEY` is passed through from `.env` (see Byte 40).

---

### Byte 19: PostgreSQL Persistence and Docker Volume

**Builds on:** Byte 18

**In plain terms:**

The PostgreSQL database stores the phonebook contacts (and the user accounts), and Docker Compose keeps the database data persistent using a volume. This means restarting or recreating the PostgreSQL container does not automatically mean that the stored contacts are lost.

**What's happening:**

The PostgreSQL service runs inside the `db` container and listens on its PostgreSQL port:

```text
PostgreSQL
    ↓
db container
    ↓
Port 5432
```

Data lives in the `pgdata` volume. `docker compose down` keeps the volume; `docker compose down -v` deletes it.

---

### Byte 20: Validation and Error Handling

**Builds on:** Byte 19

**In plain terms:**

The application validates incoming contact data before storing it in the database. This prevents invalid information from being saved and allows the API to return appropriate errors when a request cannot be processed.

**What's happening:**

The Pydantic schemas validate fields such as:

- Required contact names
- Phone number format (E.164)
- Email format
- Maximum field lengths

If the submitted data does not satisfy the validation rules, FastAPI returns a validation error (422) instead of sending invalid data to the database.

The backend also returns 404 for unknown contact IDs, 409 for duplicate phone numbers or emails, and 401 for unauthenticated requests.

**Why it matters:**

Validation protects the database from invalid input and gives the frontend a predictable way to handle unsuccessful requests.

---

### Byte 21: Backend Testing

**Builds on:** Byte 20

**In plain terms:**

The backend contains automated tests under `backend/tests`. These tests verify that important API, contact-management, and authentication functionality behaves as expected. The suite runs against a local SQLite database, so it does not need a running PostgreSQL instance.

**The structure:**

```text
backend/
└── tests/
    ├── conftest.py
    ├── test_contacts.py
    └── test_auth.py
```

`conftest.py` provides two reusable test clients: `client` (used by the contact tests, where the auth dependency is overridden so the tests focus on CRUD) and `api_client` (used by the auth tests, which exercise the real login → JWT → protected-endpoint flow). Running `python -m pytest backend` executes 26 tests covering contact CRUD, search, pagination, validation errors, duplicate phone/email handling, login success and failure, token verification, 401 responses on protected endpoints, and dashboard statistics.

**Why it matters:**

Automated tests help catch regressions. If a future code change breaks an existing feature, the tests can reveal the problem before the application is deployed.

---

### Byte 22: Frontend to Backend Communication

**Builds on:** Byte 21

**In plain terms:**

The Vue frontend and FastAPI backend communicate through HTTP API requests. The frontend does not directly access PostgreSQL. Instead, it sends requests to FastAPI, and FastAPI handles the database interaction.

**The complete flow:**

```text
User
  ↓
Vue Component
  ↓
api.js
  ↓
FastAPI API Route
  ↓
JWT Check (protected routes)
  ↓
Pydantic Validation
  ↓
CRUD Function
  ↓
SQLAlchemy
  ↓
PostgreSQL
  ↓
FastAPI Response
  ↓
Vue Component
  ↓
Updated UI
```

**What's happening:**

For example, when a user creates a contact, the Vue form collects the information and sends it through the API layer.
FastAPI receives the request, verifies the token, validates the data, and calls the appropriate CRUD operation.

The CRUD layer stores the contact in PostgreSQL and the result is returned through the API to the Vue frontend.

**Why it matters:**

This separation keeps the frontend, backend, and database independent. The browser never needs direct access to the database.

---

### Byte 23: Docker Ports and Container Communication

**Builds on:** Byte 22

**In plain terms:**

Docker gives each service its own container and allows the containers to communicate through the Docker network.
In the current project, the main exposed ports are:
Frontend → localhost:8080
Backend → localhost:8000
Database → PostgreSQL port 5432 inside Docker (not published to the host)

**What's happening:**

The frontend is accessible from the browser through:
http://localhost:8080

The FastAPI backend is accessible through:
http://localhost:8000

The backend communicates with PostgreSQL using the Docker Compose service name:
db

Therefore, inside Docker, the backend does not use localhost to reach PostgreSQL. It uses the database service name and PostgreSQL port.

The frontend container's nginx also proxies `/api/...` requests to the backend, so the browser only ever talks to the frontend origin.

**Why it matters:**

Understanding Docker networking explains why the database connection uses db:5432 inside the containers while users access the frontend through localhost:8080.

---

### Byte 24: Running the Complete Project

**Builds on:** Byte 23

**In plain terms:**

Docker Compose allows the complete Phonebook application to be started from the project root using a single command.

The command:

```bash
docker compose up -d
```

If the Docker images need to be rebuilt (for example after code changes):

```bash
docker compose up -d --build
```

To check the running containers:

```bash
docker compose ps
```

To create the first user (required before signing in):

```bash
docker compose exec backend python seed.py --create-user --username demo
```

To generate dummy contacts:

```bash
docker compose exec backend python seed.py --count 1000
```

**What's happening:**

Docker Compose starts the three main services:
db
backend
frontend

The frontend can then be opened at:
http://localhost:8080

The FastAPI Swagger documentation can be opened at:
http://localhost:8000/docs

**Why it matters:**

The project can be started consistently without manually installing and configuring PostgreSQL, Python dependencies, and the frontend server on the host machine.

---

### Byte 25: Important Edge Cases

**Builds on:** Byte 24

**In plain terms:**

A production-ready application must also consider situations where things do not go as expected.
Important cases for this project include invalid contact information, duplicate phone numbers or emails, requests for contacts that do not exist, unauthenticated requests, database connection problems, and unavailable backend services.

**Examples:**

```text
Invalid phone number
  ↓
Validation error (422)

Duplicate phone number
  ↓
Database constraint error (409)

Unknown contact ID
  ↓
Contact not found (404)

Missing/invalid/expired token
  ↓
Not authenticated (401)

Database unavailable
  ↓
Backend/database error
```

**What's happening:**

The validation layer handles many invalid inputs before they reach the database.
The database model also defines uniqueness constraints for important fields such as phone numbers and email addresses.

API and database errors need to be handled so that the frontend can display an appropriate result to the user.

**Why it matters:**

Thinking about edge cases makes an application more reliable and prevents unexpected input or system failures from causing confusing behavior.

---

### Byte 26: Putting the Complete Project Together

**Builds on:** Byte 25

**In plain terms:**

The Phonebook application is a full-stack system where each layer has a specific responsibility. Vue handles the user interface, FastAPI handles API requests and validation, SQLAlchemy handles database interaction, and PostgreSQL stores the data.

**The complete flow:**

```text
User
  ↓
Vue.js Frontend
  ↓
Vue Component
  ↓
api.js
  ↓
FastAPI Route
  ↓
JWT Check + Pydantic Schema
  ↓
CRUD Layer
  ↓
SQLAlchemy
  ↓
PostgreSQL
  ↓
Database Response
  ↓
FastAPI Response
  ↓
Vue Frontend
  ↓
Updated User Interface
```

**Why it matters:**

The separation of responsibilities makes the project easier to understand, test, maintain, and deploy.

Docker Compose brings the complete environment together by running the frontend, backend, and PostgreSQL database as connected services.

---

### Byte 27: User Accounts and Password Hashing

**Builds on:** Byte 26

**In plain terms:**

The application has user accounts. A user signs in once with a username (or email) and password, and the backend stores only a bcrypt hash of the password — never the password itself. The `users` table is separate from the `contacts` table, so user accounts and contacts are independent.

**The code:**

```python
class User(Base):
    """Application user for authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

Passwords are hashed with bcrypt in `backend/app/auth.py`:

```python
def get_password_hash(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
```

There are no users by default — the first user is created with the seed script (Byte 39).

---

### Byte 28: JWT Access Tokens

**Builds on:** Byte 27

**In plain terms:**

After a successful login the backend issues a JSON Web Token (JWT). The token is signed with a secret key and expires after 12 hours. Because the JWT is self-contained, the backend keeps no session state — it only verifies the signature on each request.

**The code:**

```python
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720  # 12 hours


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

The signing key comes from the `SECRET_KEY` environment variable (see Byte 40). If it is not set, an ephemeral random key is generated on each start, which means tokens stop working after a backend restart.

---

### Byte 29: Logging In — `POST /auth/login`

**Builds on:** Byte 28

**In plain terms:**

The login endpoint accepts a username or an email address plus a password. It looks up the user, checks the password against the stored bcrypt hash, and returns a JWT together with the user's public profile. Wrong credentials always produce the same generic 401 message.

**The code:**

```python
@app.post("/auth/login")
def login(login_request: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with a username or email and return a JWT access token."""
    identifier = login_request.username
    user = (
        db.query(models.User)
        .filter(
            (models.User.username == identifier) | (models.User.email == identifier)
        )
        .first()
    )
    if user is None or not auth_utils.verify_password(
        login_request.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401, detail="Incorrect username/email or password"
        )
    token = auth_utils.create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": schemas.UserResponse.model_validate(user).model_dump(),
    }
```

The token payload uses the standard `sub` (subject) claim for the username and `exp` for the expiry time.

---

### Byte 30: Protecting API Routes with Dependencies

**Builds on:** Byte 29

**In plain terms:**

Every contact and statistics endpoint requires a valid JWT. FastAPI's dependency system makes this a one-line addition per route: `dependencies=[Depends(auth_utils.get_current_user)]`. The `get_current_user` function reads the `Authorization: Bearer <token>` header, verifies the JWT, and loads the user — or raises 401.

**The code:**

```python
@app.get("/contacts", response_model=list[schemas.ContactResponse],
         dependencies=[Depends(auth_utils.get_current_user)])
def list_contacts(...):
    ...
```

```python
def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> models.User:
    """Return the user for a valid Bearer token, else raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
```

Related endpoints: `GET /auth/me` returns the currently signed-in user (using the same dependency as a parameter), and `POST /auth/logout` simply returns a message — the client discards its token because JWTs are stateless.

---

### Byte 31: Frontend Authentication State — `auth.js`

**Builds on:** Byte 30

**In plain terms:**

`frontend/src/auth.js` holds the signed-in state of the frontend. After login, the JWT and the user profile are stored in the browser's localStorage, so the user stays signed in across page refreshes. Every Vue component can import the shared reactive `auth` object.

**The code:**

```javascript
const TOKEN_KEY = 'phonebook_token'
const USER_KEY = 'phonebook_user'

export const auth = reactive({
  token: localStorage.getItem(TOKEN_KEY) || null,
  user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
  loggingIn: false
})

export function setAuth(token, user) {
  auth.token = token
  auth.user = user
  localStorage.setItem(TOKEN_KEY, token)
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  auth.token = null
  auth.user = null
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}
```

The file also exports `initialsOf(user)`, which turns a username into the two-letter avatar shown in the sidebar and on the account page.

---

### Byte 32: Automatic Token Attachment and 401 Handling

**Builds on:** Byte 31

**In plain terms:**

The axios instance in `api.js` uses interceptors so that no component has to handle tokens manually. Every outgoing request automatically gets the `Authorization: Bearer <token>` header when a token exists, and every 401 response clears the stored session and notifies the app — which redirects to the login page.

**The code:**

```javascript
api.interceptors.request.use((config) => {
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuth()
      if (unauthorizedHandler) unauthorizedHandler()
    }
    return Promise.reject(error)
  }
)
```

The `unauthorizedHandler` is registered in `main.js` (Byte 12) and performs the redirect to the login route.

---

### Byte 33: Protecting Frontend Routes — the Navigation Guard

**Builds on:** Byte 32

**In plain terms:**

Even with protected API endpoints, the frontend must not show protected pages to a signed-out user. A Vue Router guard checks the `requiresAuth` metadata of each route before navigation and redirects to the login page — remembering the originally requested URL so the user can be sent back after signing in. Signed-in users who open the login page are sent to the dashboard instead.

**The code:**

```javascript
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isAuthenticated.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && isAuthenticated.value) {
    return { name: 'dashboard' }
  }
})
```

---

### Byte 34: The Login Screen — `LoginView.vue`

**Builds on:** Byte 33

**In plain terms:**

`frontend/src/views/LoginView.vue` is the sign-in page. It collects an email-or-username and a password, validates that both are filled in, calls the login API, stores the returned token with `setAuth`, and navigates to the dashboard (or back to the page the user originally requested). Errors such as a wrong password are shown on the page.

**The code:**

```javascript
async function submit() {
  serverError.value = ''
  if (!validate()) return

  loading.value = true
  try {
    const { data } = await api.login({
      username: form.username,
      password: form.password
    })
    setAuth(data.access_token, data.user)
    const redirect = typeof route.query.redirect === 'string'
      ? route.query.redirect
      : { name: 'dashboard' }
    router.push(redirect)
  } catch (e) {
    const message = extractError(e)
    serverError.value =
      message === 'Not authenticated'
        ? 'Incorrect email/username or password.'
        : message
  } finally {
    loading.value = false
  }
}
```

The form shows a "Signing in..." spinner while the request is in flight.

---

### Byte 35: Dashboard Statistics — `GET /stats`

**Builds on:** Byte 34

**In plain terms:**

The dashboard shows live statistics that the backend calculates from the database: the total number of contacts, how many were added in the last 7 days, how many have an email address, how many have a phone number, and the 5 most recently added contacts.

**The code:**

```python
@app.get("/stats", response_model=schemas.StatsResponse,
         dependencies=[Depends(auth_utils.get_current_user)])
def get_stats(db: Session = Depends(get_db)):
    """Phonebook statistics for the dashboard."""
    return schemas.StatsResponse(
        total_contacts=crud.count_contacts(db),
        recent_contacts=crud.count_contacts_recent(db),
        with_email=crud.count_contacts_with_field(db, models.Contact.email),
        with_phone=crud.count_contacts_with_field(db, models.Contact.phone_number),
        recent_list=crud.get_recent_contacts(db),
    )
```

The counting queries live in `crud.py`:

```python
def count_contacts_recent(db: Session, *, days: int = 7) -> int:
    """Contacts created within the last `days` days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return db.query(models.Contact).filter(models.Contact.created_at >= since).count()
```

---

### Byte 36: The Dashboard View — `DashboardView.vue`

**Builds on:** Byte 35

**In plain terms:**

`frontend/src/views/DashboardView.vue` is the landing page after sign-in. It fetches `/stats` when the page loads and renders four stat cards (total contacts, added in the last 7 days, with email, with phone) plus a list of the most recent contacts. Loading, error, and empty states are handled explicitly — the empty state offers a link to add the first contact.

**The code:**

```javascript
async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.getStats()
    stats.value = data
  } catch (e) {
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
```

---

### Byte 37: Responsive Navigation — Sidebar and Hamburger Menu

**Builds on:** Byte 36

**In plain terms:**

The application shell in `App.vue` provides the menu. On wide screens the sidebar is always visible; on narrow screens it hides behind a hamburger button and slides in as an overlay with a backdrop. The menu contains Dashboard, Contacts, Add Contact, and Account links, a user chip showing the signed-in username, and a Logout button. Vue Router automatically highlights the active page, and the menu closes whenever the route changes.

**The code:**

```vue
<nav class="sidebar-nav">
  <router-link to="/" class="nav-item">Dashboard</router-link>
  <router-link to="/contacts" class="nav-item">Contacts</router-link>
  <router-link to="/contacts/new" class="nav-item">Add Contact</router-link>
  <router-link to="/profile" class="nav-item">Account</router-link>
</nav>
```

```javascript
async function handleLogout() {
  try {
    await api.logout()
  } catch (e) {
    // The token is discarded locally regardless; the API call is
    // best-effort (JWTs are stateless on the server).
    console.warn('Logout request failed:', extractError(e))
  }
  clearAuth()
  router.push({ name: 'login' })
}
```

The login page shows no navigation at all — the sidebar and top bar are rendered only when `auth.user` is set.

---

### Byte 38: Editing a Contact — `ContactDetail.vue`

**Builds on:** Byte 37

**In plain terms:**

`frontend/src/views/ContactDetail.vue` is both the detail view and the edit form for one contact. It loads the contact by its ID from the URL (`/contacts/:id`), fills the form with the existing values, validates the fields (name required, phone in E.164 format, optional email), and sends the changes with a PUT request. After saving, the page shows the updated contact.

**The code:**

```javascript
async function save() {
  serverError.value = ''
  if (!validate()) return
  saving.value = true
  try {
    const { data } = await api.updateContact(route.params.id, payload())
    contact.value = data
    reset()
  } catch (e) {
    serverError.value = extractError(e)
  } finally {
    saving.value = false
  }
}
```

Empty optional fields are sent as `null` so they are cleared in the database. The avatar next to the contact name is built by an `initials` helper defined in the same component (ContactList.vue and DashboardView.vue define the same helper for their own avatars).

---

### Byte 39: Generating Dummy Data — `seed.py`

**Builds on:** Byte 38

**In plain terms:**

`backend/seed.py` is a command-line tool for setting up demo data. It can create the first user (the password is prompted for if not supplied) and generate thousands of realistic dummy contacts with Faker. Generated phone numbers and emails are checked against existing rows, so the script never duplicates or modifies existing contacts. It is run manually — it does not run on application startup.

**The code:**

```python
def generate_contacts(db, count: int) -> int:
    """Generate `count` dummy contacts without touching existing data."""
    fake = Faker()
    existing_phones = {row[0] for row in db.query(models.Contact.phone_number)}
    existing_emails = {
        row[0] for row in db.query(models.Contact.email) if row[0] is not None
    }
    used_phones = set(existing_phones)
    used_emails = set(existing_emails)

    batch = []
    created = 0
    attempts = 0
    while created < count and attempts < count * 20:
        attempts += 1

        phone = _random_phone()
        if phone in used_phones:
            continue
        ...
```

Contacts are inserted in batches of 500 so large runs stay memory-friendly. Usage:

```bash
python seed.py --create-user --username demo            # prompts for a password
python seed.py --create-user --username demo --password 'choose-a-password'
python seed.py --count 100                              # 100 dummy contacts
python seed.py --count 1000                             # 1,000 dummy contacts
python seed.py --count 5000                             # 5,000 dummy contacts
```

Inside Docker the same script runs in the backend container:

```bash
docker compose exec backend python seed.py --create-user --username demo
docker compose exec backend python seed.py --count 1000
```

Both actions can be combined in one run. The script has been used to generate 100 and 1,000 contacts (and verified up to 5,000) with pagination and search still responding quickly.

---

### Byte 40: Environment Variables and `SECRET_KEY`

**Builds on:** Byte 39

**In plain terms:**

Configuration lives in `.env` (see `.env.example`): the PostgreSQL credentials shared by the `db` container and the backend, and the `SECRET_KEY` used to sign JWTs. Docker Compose passes these values into the containers, so no secret is hardcoded in the source code.

**The code:**

```
# Database credentials used by both the PostgreSQL container and the backend.
POSTGRES_USER=phonebook
POSTGRES_PASSWORD=phonebook
POSTGRES_DB=phonebook

# Secret key used to sign the JWT authentication tokens.
# Replace with a long random string, e.g.: python -c "import secrets; print(secrets.token_hex(32))"
# If left empty, the backend generates an ephemeral key on each start
# (fine for demos, but users will have to log in again after a restart).
SECRET_KEY=
```

```yaml
    environment:
      DATABASE_URL: postgresql+psycopg2://${POSTGRES_USER:-phonebook}:${POSTGRES_PASSWORD:-phonebook}@db:5432/${POSTGRES_DB:-phonebook}
      SECRET_KEY: ${SECRET_KEY:-}
```

The backend dependencies for authentication are `python-jose[cryptography]` (JWT signing/verification) and `bcrypt` (password hashing); `Faker` powers the seed script.

---

### Byte 41: The Complete Picture

**Builds on:** Byte 40

**In plain terms:**

The Phonebook application is a full-stack system where each layer has a specific responsibility — now with authentication, a dashboard, responsive navigation, and a data generator on top of the original contact CRUD.

**The complete flow:**

```text
User
  ↓
Vue.js Frontend (login page → token in localStorage)
  ↓
api.js (adds Bearer token to every request)
  ↓
FastAPI Route (JWT verified by get_current_user)
  ↓
Pydantic Schema
  ↓
CRUD Layer
  ↓
SQLAlchemy
  ↓
PostgreSQL
  ↓
Database Response
  ↓
FastAPI Response
  ↓
Vue Frontend
  ↓
Updated User Interface
```

**API summary:**

| Endpoint | Purpose | Auth |
| --- | --- | --- |
| `GET /health` | Health check | — |
| `POST /auth/login` | Sign in, returns a JWT | — |
| `GET /auth/me` | Current signed-in user | ✓ |
| `POST /auth/logout` | Sign out (client discards token) | — |
| `GET /stats` | Dashboard statistics + recent contacts | ✓ |
| `GET /contacts` | List contacts (`page`, `page_size`, `q`; total in `X-Total-Count`) | ✓ |
| `POST /contacts` | Add a contact | ✓ |
| `GET /contacts/{id}` | Get one contact | ✓ |
| `PUT /contacts/{id}` | Update a contact | ✓ |
| `DELETE /contacts/{id}` | Delete a contact | ✓ |

**Why it matters:**

The separation of responsibilities makes the project easier to understand, test, maintain, and deploy. Docker Compose brings the complete environment together — frontend, backend, and PostgreSQL — so the application can be started consistently with `docker compose up -d --build`.

PUTTING IT TOGETHER
The user signs in through the Vue.js login screen, which stores the JWT returned by FastAPI in localStorage. Vue sends API requests with the token to the FastAPI backend, which verifies the JWT, validates the data using Pydantic schemas, and delegates database operations to the CRUD layer. SQLAlchemy communicates with PostgreSQL, where contacts and user accounts are stored persistently. The dashboard reads live statistics from the backend, the seed script generates thousands of dummy contacts for testing, and Docker Compose runs the frontend, backend, and PostgreSQL services together so the complete application can be started consistently.
