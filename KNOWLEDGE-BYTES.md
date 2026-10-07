# Phonebook Python — Knowledge Bytes

> Notes explaining the Phonebook project step by step

---

### Byte 1: Overall Project Architecture

**Builds on:** None — starting point

**In plain terms:**

This Phonebook project is a full-stack web application. The user manages contacts through the frontend, the frontend sends requests to the FastAPI backend, the backend communicates with the PostgreSQL database, and the result is returned to the frontend.

**The architecture:**

```text
User
  ↓
Vue.js Frontend
  ↓
FastAPI Backend
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
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── crud.py
│   │
│   └── tests/
│       ├── conftest.py
│       └── test_contacts.py
│
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router.js
│   │   ├── api.js
│   │   └── views/
│   │       ├── ContactList.vue
│   │       ├── ContactDetail.vue
│   │       └── CreateContact.vue
│   │
│   ├── Dockerfile
│   ├── nginx.conf
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

`backend/app/main.py` is the main entry point of the FastAPI backend. It creates the FastAPI application and defines the API endpoints that the frontend can call.

**The code:**

```python
app = FastAPI(
    title="Phonebook API",
    version="1.0.0",
    lifespan=lifespan
)



```

---

### Byte 4: API Data Validation — `schemas.py`

**Builds on:** Byte 3

**In plain terms:**

`backend/app/schemas.py` defines the structure and validation rules for data entering and leaving the API. It uses Pydantic models to make sure that contact data has the expected format before the backend processes it.

**The code:**

```python
class ContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone_number: str = Field(..., pattern=PHONE_NUMBER_PATTERN)
    email: Optional[EmailStr] = None
    address: Optional[str] = None



```

---

### Byte 5: Database Model — `models.py`

**Builds on:** Byte 4

**In plain terms:**

`backend/app/models.py` defines the database model for a phonebook contact. The `Contact` class represents a row in the PostgreSQL `contacts` table.

**The code:**

```python
class Contact(Base):
    """A single phonebook entry."""

    __tablename__ = "contacts"




```

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

---

### Byte 7: Database Operations — `crud.py`

**Builds on:** Byte 6

**In plain terms:**

`backend/app/crud.py` contains the functions that perform database operations for contacts. Instead of putting database queries directly inside the API routes, the project keeps these operations in a separate CRUD layer.

**The code:**

The CRUD layer works with a SQLAlchemy database session and the `Contact` model.

A typical create operation follows this pattern:

```python
db_contact = models.Contact(**contact_data)
db.add(db_contact)
db.commit()
db.refresh(db_contact)
return db_contact



```

---

### Byte 8: Creating a Contact Through the API

**Builds on:** Byte 7

**In plain terms:**

When the frontend wants to create a new contact, it sends the contact information to the FastAPI backend. The backend receives the request, validates the data using the schema, and then uses the CRUD layer to save the contact in PostgreSQL.

**The flow:**

```text
Vue Frontend
     ↓
POST API Request
     ↓
FastAPI Route
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

---

### Byte 9: Reading Contacts from the API

**Builds on:** Byte 8

**In plain terms:**

The application also needs to retrieve contacts from PostgreSQL and display them in the frontend. The frontend sends a GET request to the FastAPI backend, and the backend retrieves the required contacts through the CRUD layer.

**The flow:**

```text
Vue Frontend
     ↓
GET API Request
     ↓
FastAPI Route
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

---

### Byte 10: Updating a Contact

**Builds on:** Byte 9

**In plain terms:**

The Phonebook application allows an existing contact to be edited. The frontend sends the contact ID and the updated information to the FastAPI backend, which validates the data and updates the corresponding record in PostgreSQL.

**The flow:**

```text
Vue Frontend
     ↓
PUT API Request
     ↓
FastAPI Route
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

---

### Byte 11: Deleting a Contact

**Builds on:** Byte 10

**In plain terms:**

The Phonebook application also allows the user to remove an existing contact. The frontend sends a delete request for a specific contact, and the backend removes that record from PostgreSQL through the CRUD layer.

**The flow:**

```text
Vue Frontend
     ↓
DELETE API Request
     ↓
FastAPI Route
     ↓
CRUD Delete Operation
     ↓
PostgreSQL
     ↓
Response
     ↓
Vue Frontend
```

---

### Byte 12: Frontend Entry Point — `main.js`

**Builds on:** Byte 11

**In plain terms:**

`frontend/src/main.js` is the entry point of the Vue.js frontend. It creates the Vue application and connects the application to the main `App.vue` component.

**The code:**

```javascript
import { createApp } from "vue";
import App from "./App.vue";

createApp(App).mount("#app");
```

---

### Byte 13: API Communication — `api.js`

**Builds on:** Byte 12

**In plain terms:**

`frontend/src/api.js` is responsible for communicating with the FastAPI backend. Instead of writing HTTP request code separately inside every Vue component, the frontend keeps the API-related logic in one place.

**The code:**

```javascript
const API_BASE_URL = "/api";
```

---

### Byte 14: Vue Application Root — `App.vue`

**Builds on:** Byte 13

**In plain terms:**

`frontend/src/App.vue` is the main/root Vue component of the application. It provides the common structure of the frontend and acts as the parent component for the different pages displayed through the router.

**The code:**

```vue
<template>
  <router-view />
</template>
```

---

### Byte 15: Frontend Routing — `router.js`

**Builds on:** Byte 14

**In plain terms:**

`frontend/src/router.js` defines the routes of the Vue application. It connects browser URLs to the Vue components that should be displayed.

**The code:**

```javascript
const routes = [
  {
    path: "/",
    redirect: "/contacts",
  },
  // Other application routes
];
```

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

---

### Byte 17: Contact Creation and Detail Views

**Builds on:** Byte 16

**In plain terms:**

The frontend has separate views for creating a new contact and viewing the details of an existing contact. This keeps different user actions separated into focused Vue components.

**The files:**

```text
frontend/src/views/
├── CreateContact.vue
├── ContactDetail.vue
└── ContactList.vue




```

---

### Byte 18: Docker Compose — Running the Complete Application

**Builds on:** Byte 17

**In plain terms:**

`docker-compose.yml` defines the services required to run the Phonebook application together. Instead of manually installing and starting PostgreSQL, the FastAPI backend, and the frontend separately, Docker Compose manages them as connected services.

**The structure:**

```yaml
services:
  db:
    image: postgres:16-alpine

  backend:
    build: ./backend

  frontend:
    build: ./frontend
```

---

### Byte 19: PostgreSQL Persistence and Docker Volume

**Builds on:** Byte 18

**In plain terms:**

The PostgreSQL database stores the phonebook contacts, and Docker Compose keeps the database data persistent using a volume. This means restarting or recreating the PostgreSQL container does not automatically mean that the stored contacts are lost.

**What's happening:**

The PostgreSQL service runs inside the `db` container and listens on its PostgreSQL port:

```text
PostgreSQL
    ↓
db container
    ↓
Port 5432
```

---

### Byte 20: Validation and Error Handling

**Builds on:** Byte 19

**In plain terms:**

The application validates incoming contact data before storing it in the database. This prevents invalid information from being saved and allows the API to return appropriate errors when a request cannot be processed.

**What's happening:**

The Pydantic schemas validate fields such as:

- Required contact names
- Phone number format
- Email format
- Maximum field lengths

If the submitted data does not satisfy the validation rules, FastAPI returns a validation error instead of sending invalid data to the database.

The backend can also handle situations such as a contact not being found or an operation failing.

**Why it matters:**

Validation protects the database from invalid input and gives the frontend a predictable way to handle unsuccessful requests.

---

### Byte 21: Backend Testing

**Builds on:** Byte 20

**In plain terms:**

The backend contains automated tests under `backend/tests`. These tests verify that important API and contact-management functionality behaves as expected.

**The structure:**

```text
backend/
└── tests/
    ├── conftest.py
    └── test_contacts.py



```

What's happening:
conftest.py provides test configuration and reusable test setup.
test_contacts.py contains tests for contact-related functionality.
The tests help verify that operations such as creating, reading, updating, and deleting contacts continue to work correctly.

Why it matters:
Automated tests help catch regressions. If a future code change breaks an existing feature, the tests can reveal the problem before the application is deployed.

Byte 22: Frontend to Backend Communication
Builds on: Byte 21
In plain terms:
The Vue frontend and FastAPI backend communicate through HTTP API requests. The frontend does not directly access PostgreSQL. Instead, it sends requests to FastAPI, and FastAPI handles the database interaction.
The complete flow:
User
↓
Vue Component
↓
api.js
↓
FastAPI API Route
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

What's happening:
For example, when a user creates a contact, the Vue form collects the information and sends it through the API layer.
FastAPI receives the request, validates the data, and calls the appropriate CRUD operation.

The CRUD layer stores the contact in PostgreSQL and the result is returned through the API to the Vue frontend.

Why it matters:
This separation keeps the frontend, backend, and database independent. The browser never needs direct access to the database.

Byte 23: Docker Ports and Container Communication

Builds on: Byte 22

In plain terms:
Docker gives each service its own container and allows the containers to communicate through the Docker network.
In the current project, the main exposed ports are:
Frontend → localhost:8080
Backend → localhost:8000
Database → PostgreSQL port 5432 inside Docker

What's happening:
The frontend is accessible from the browser through:
http://localhost:8080

The FastAPI backend is accessible through:
http://localhost:8000

The backend communicates with PostgreSQL using the Docker Compose service name:
db

Therefore, inside Docker, the backend does not use localhost to reach PostgreSQL. It uses the database service name and PostgreSQL port.

Why it matters:
Understanding Docker networking explains why the database connection uses db:5432 inside the containers while users access the frontend through localhost:8080.

Byte 24: Running the Complete Project

Builds on: Byte 23

In plain terms:
Docker Compose allows the complete Phonebook application to be started from the project root using a single command.
The command:
docker compose up -d

If the Docker images need to be rebuilt:
docker compose up -d --build

To check the running containers:
docker compose ps

What's happening:
Docker Compose starts the three main services:
db
backend
frontend

The frontend can then be opened at:
http://localhost:8080

The FastAPI Swagger documentation can be opened at:
http://localhost:8000/docs

Why it matters:
The project can be started consistently without manually installing and configuring PostgreSQL, Python dependencies, and the frontend server on the host machine.

Byte 25: Important Edge Cases

Builds on: Byte 24

In plain terms:
A production-ready application must also consider situations where things do not go as expected.
Important cases for this project include invalid contact information, duplicate phone numbers or emails, requests for contacts that do not exist, database connection problems, and unavailable backend services.

Examples:
Invalid phone number
↓
Validation error

Duplicate phone number
↓
Database constraint/error

Unknown contact ID
↓
Contact not found

Database unavailable
↓
Backend/database error

What's happening:
The validation layer handles many invalid inputs before they reach the database.
The database model also defines uniqueness constraints for important fields such as phone numbers and email addresses.

API and database errors need to be handled so that the frontend can display an appropriate result to the user.

Why it matters:
Thinking about edge cases makes an application more reliable and prevents unexpected input or system failures from causing confusing behavior.

Byte 26: Putting the Complete Project Together

Builds on: Byte 25

In plain terms:
The Phonebook application is a full-stack system where each layer has a specific responsibility. Vue handles the user interface, FastAPI handles API requests and validation, SQLAlchemy handles database interaction, and PostgreSQL stores the data.
The complete flow:
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

Why it matters:
The separation of responsibilities makes the project easier to understand, test, maintain, and deploy.

Docker Compose brings the complete environment together by running the frontend, backend, and PostgreSQL database as connected services.

PUTTING IT TOGETHER
The user interacts with the Phonebook through the Vue.js frontend. Vue sends API requests to the FastAPI backend instead of communicating directly with PostgreSQL. FastAPI validates the incoming data using Pydantic schemas and delegates database operations to the CRUD layer. SQLAlchemy communicates with PostgreSQL, where the contact data is stored persistently. The result travels back through FastAPI to the Vue frontend, which updates the user interface. Docker Compose runs the frontend, backend, and PostgreSQL services together so the complete application can be started consistently.
