# Simple LMS (Learning Management System)

Aplikasi Django berbasis web untuk Learning Management System dengan dukungan PostgreSQL dan Redis caching.

## 📋 Daftar Isi

- [Fitur](#fitur)
- [Tech Stack](#tech-stack)
- [Prasyarat](#prasyarat)
- [Cara Menjalankan Project](#cara-menjalankan-project)
- [Struktur Direktori](#struktur-direktori)
- [Environment Variables](#environment-variables)
- [Services & Endpoints](#services--endpoints)
- [Database Management](#database-management)
- [Admin Credentials](#admin-credentials)
- [Troubleshooting](#troubleshooting)

---

## ✨ Fitur

- ✅ Web Framework Django 4.2.0
- ✅ PostgreSQL 15 Database dengan health check
- ✅ Redis 7 untuk Caching & Session Management
- ✅ Django Admin Panel untuk management
- ✅ pgAdmin untuk Database Management UI
- ✅ Docker & Docker Compose untuk containerization
- ✅ Health Check Endpoint untuk monitoring

---

## 🛠️ Tech Stack

| Komponen | Version | Purpose |
|----------|---------|---------|
| **Django** | 4.2.0 | Web Framework |
| **PostgreSQL** | 15-alpine | Database |
| **Redis** | 7-alpine | Cache & Session Store |
| **Python** | 3.11-slim | Runtime |
| **Docker** | Latest | Container Platform |
| **pgAdmin** | Latest | Database UI |

---

## 📦 Prasyarat

Pastikan sudah terinstall:

- **Docker** (v20.10+) - [Download](https://www.docker.com/products/docker-desktop)
- **Docker Compose** (v1.29+) - Biasanya included dengan Docker Desktop
- **Git** (optional) - untuk clone project

Verifikasi instalasi:
```bash
docker --version
docker-compose --version
```

---

## 🚀 Cara Menjalankan Project

### 1️⃣ Clone atau Download Project

```bash
cd simple-lms
```

### 2️⃣ Jalankan dengan Docker Compose

```bash
docker-compose up -d
```

**Output jika sukses:**
```
[+] Running 4/4
 ✓ Container lms_database  Healthy
 ✓ Container lms_redis     Started
 ✓ Container simple_lms    Started
 ✓ Container lms_pgadmin   Started
```

### 3️⃣ Migrasi Database (First Time Only)

```bash
docker-compose exec -T app python manage.py migrate
```

### 4️⃣ Buat Superuser Admin (First Time Only)

Opsional - jika sudah ada skip step ini:

```bash
docker-compose exec app python manage.py createsuperuser
```

Atau gunakan script otomatis:
```bash
docker-compose exec -T app python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"
```

### 5️⃣ Akses Aplikasi

| Service | URL | Port |
|---------|-----|------|
| **Django App** | http://localhost:8000 | 8000 |
| **Admin Panel** | http://localhost:8000/admin | 8000 |
| **pgAdmin** | http://localhost:5050 | 5050 |

---

## 📁 Struktur Direktori

```
simple-lms/
├── docker-compose.yml      # Docker service configuration
├── Dockerfile              # Django app container definition
├── manage.py               # Django management command
├── requirement.txt         # Python dependencies
├── README.md              # This file
├── config/
│   ├── __init__.py        # Python package marker
│   ├── settings.py        # Django settings (DB, cache, etc)
│   ├── urls.py            # URL routing & endpoints
│   └── wsgi.py            # WSGI application
└── [data volumes]
    ├── postgres_data      # PostgreSQL persistent data
    └── redis_data         # Redis persistent data
```

---

## 🔧 Environment Variables

Environment variables diatur di `docker-compose.yml` pada service `app`:

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| **DEBUG** | `True` | Django debug mode (ubah ke `False` di production) |
| **DATABASE_URL** | `postgres://postgres:postgres@database:5432/lms_db` | PostgreSQL connection string |
| **REDIS_URL** | `redis://redis:6379/0` | Redis connection string |
| **SECRET_KEY** | `django-insecure-dev-key-change-in-production` | Django secret key untuk security |

### Mengubah Environment Variables

Edit `docker-compose.yml` pada section `app` → `environment`:

```yaml
environment:
  - DEBUG=False  # Ubah ke False untuk production
  - DATABASE_URL=postgres://postgres:postgres@database:5432/lms_db
  - REDIS_URL=redis://redis:6379/0
  - SECRET_KEY=your-secret-key-here
```

Kemudian restart containers:
```bash
docker-compose up -d --build
```

---

## 🌐 Services & Endpoints

### Django Application

**Home Page**
```
GET http://localhost:8000/
```
Response:
```json
{
  "message": "Welcome to Simple LMS",
  "endpoints": {
    "health": "/health/",
    "cached": "/cached/",
    "admin": "/admin/"
  }
}
```

**Health Check Endpoint**
```
GET http://localhost:8000/health/
```
Verifikasi semua services (Database, Redis, Cache):
```json
{
  "status": "ok",
  "message": "Simple LMS Application is running",
  "services": {
    "database": "✓ Connected",
    "redis": "✓ Connected",
    "cache": "✓ Working"
  }
}
```

**Cached Endpoint (Testing Cache)**
```
GET http://localhost:8000/cached/
```
Response (dikache selama 60 detik):
```json
{
  "message": "This response is cached for 60 seconds",
  "timestamp": 1776409340.7572258
}
```

**Django Admin Panel**
```
GET/POST http://localhost:8000/admin/
```

---

## 💾 Database Management

### 📊 Opsi 1: pgAdmin UI (Recommended)

Akses web interface:
- **URL**: http://localhost:5050
- **Email**: `admin@example.com`
- **Password**: `admin123`

**Setup Server pertama kali:**

1. Klik **Add New Server**
2. Isi tab **General**:
   - Name: `lms_db`

3. Isi tab **Connection**:
   - Host: `database`
   - Port: `5432`
   - Username: `postgres`
   - Password: `postgres`
   - Database: `lms_db`

4. Klik **Save**
5. Explore di sidebar: `Servers` → `lms_db` → `Databases` → `lms_db` → `Schemas` → `public` → `Tables`

### 🖥️ Opsi 2: Command Line (psql)

**Lihat semua tables:**
```bash
docker-compose exec -T database psql -U postgres -d lms_db -c "\dt"
```

**Lihat data users:**
```bash
docker-compose exec -T database psql -U postgres -d lms_db -c "SELECT id, username, email, is_superuser FROM auth_user;"
```

**Lihat structure table:**
```bash
docker-compose exec -T database psql -U postgres -d lms_db -c "\d auth_user"
```

**Run custom query:**
```bash
docker-compose exec -T database psql -U postgres -d lms_db -c "SELECT * FROM django_session LIMIT 5;"
```

**Exit psql:**
```
\q
```

---

## 👤 Admin Credentials

Akses Django Admin Panel dengan:

| Field | Value |
|-------|-------|
| **URL** | http://localhost:8000/admin/ |
| **Username** | `admin` |
| **Password** | `admin123` |
| **Email** | `admin@example.com` |

**Gunakan untuk:**
- ✅ Manage users, groups, permissions
- ✅ View admin logs
- ✅ Manage sessions
- ✅ Configure content types

---

## 🖼️ Screenshots

### Django Welcome Page

![Welcome Page](./ss/wp.png)


## 🔍 Troubleshooting

### ❌ Error: "database files are incompatible"

**Penyebab**: PostgreSQL version mismatch (old data dengan new image)

**Solusi**:
```bash
# Stop dan hapus volumes
docker-compose down -v

# Restart fresh
docker-compose up -d
```

### ❌ Port 8000 sudah digunakan

**Penyebab**: Aplikasi lain sudah menggunakan port 8000

**Solusi**: Ubah port di `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Ubah dari 8000 menjadi 8001
```

### ❌ Port 5050 sudah digunakan (pgAdmin)

**Solusi**: Ubah port pgAdmin di `docker-compose.yml`:
```yaml
pgadmin:
  ports:
    - "5051:80"  # Ubah dari 5050 menjadi 5051
```

### ❌ Container berhenti dengan error

**Debug dengan logs:**
```bash
# Lihat logs semua service
docker-compose logs

# Lihat logs specific service
docker-compose logs app
docker-compose logs database
docker-compose logs redis
docker-compose logs pgadmin
```

### ❌ Tidak bisa connect ke database dari outside

**Pastikan**:
- Database container running: `docker-compose ps`
- Database port: `5432` accessible
- Credentials benar: `postgres` / `postgres`
- Database name: `lms_db`

---

## 📝 Commands Berguna

```bash
# Status semua containers
docker-compose ps

# Lihat logs real-time
docker-compose logs -f app

# Stop semua services
docker-compose stop

# Start services kembali
docker-compose start

# Rebuild containers
docker-compose up -d --build

# Remove semua containers & volumes
docker-compose down -v

# Akses shell Django
docker-compose exec app python manage.py shell

# Collect static files
docker-compose exec app python manage.py collectstatic

# Create custom migration
docker-compose exec app python manage.py makemigrations

# Apply migrations
docker-compose exec app python manage.py migrate
```

---

## 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Docker Documentation](https://docs.docker.com/)

---

## 📄 License

MIT License - Silahkan gunakan project ini untuk keperluan pembelajaran.

---

## ❓ Support

Untuk bantuan atau pertanyaan:
1. Cek bagian [Troubleshooting](#troubleshooting)
2. Lihat Docker logs: `docker-compose logs`
3. Verifikasi environment variables di `docker-compose.yml`

---
