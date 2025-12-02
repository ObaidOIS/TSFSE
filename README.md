# 📰 Bloomberg News Scraper & AI-Powered Search Engine

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-5.0-green?style=for-the-badge&logo=django)
![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue?style=for-the-badge&logo=typescript)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?style=for-the-badge&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-red?style=for-the-badge&logo=redis)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)

**A full-stack news aggregation platform with AI-powered categorization and intelligent search**

[Features](#-features) • [Tech Stack](#-tech-stack) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Architecture](#-architecture)

</div>

---

## 🌟 Features

### 📊 Intelligent News Aggregation
- **Automated Bloomberg Scraping**: RSS feed parsing with intelligent content extraction
- **Real-time Updates**: Celery-based periodic scraping (every 5 minutes)
- **Duplicate Detection**: Smart deduplication using URL hashing and content similarity
- **Change Detection**: Monitors article updates and tracks content changes

### 🤖 AI-Powered Categorization
- **Lightweight Keyword-Based AI**: Fast, efficient categorization without heavy ML dependencies
- **Multi-Category Support**: Economy, Market, Health, Technology, Industry, and more
- **Confidence Scoring**: Each article includes AI confidence percentage
- **Keyword Extraction**: Intelligent keyword and entity extraction from article content

### 🔍 Advanced Search Engine
- **Full-Text Search**: PostgreSQL tsvector for fast, accurate searches
- **Auto-Category Detection**: AI automatically detects category from search queries
- **Relevance Ranking**: BM25-inspired scoring with multiple ranking factors
- **Real-time Suggestions**: Search autocomplete with category predictions

### 🎨 Modern Frontend
- **Next.js 14 App Router**: Latest React Server Components
- **Responsive Design**: Mobile-first with TailwindCSS
- **Bloomberg-Inspired UI**: Professional financial news aesthetic
- **Optimized Performance**: React Query for caching and state management

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|------------|----------|
| **Python 3.11+** | Core programming language |
| **Django 5.0** | Web framework |
| **Django REST Framework** | API development |
| **Celery + Flower** | Async task processing with monitoring |
| **Redis** | Caching & message broker |
| **PostgreSQL 16** | Primary database with FTS & pg_trgm |
| **Whitenoise** | Static file serving |
| **Structlog** | Structured logging |
| **BeautifulSoup4** | Web scraping |
| **feedparser** | RSS feed parsing |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 14** | React framework |
| **React 18** | UI library |
| **TypeScript 5.3** | Type safety |
| **TailwindCSS 3.4** | Styling |
| **React Query** | Server state management |
| **Axios** | HTTP client |
| **Lucide React** | Icons |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Orchestration |
| **Nginx** | Reverse proxy |
| **Gunicorn** | WSGI server |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/ObaidOIS/TSFSE.git
cd TSFSE
```

### 2. Environment Setup
```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit .env with your settings
nano backend/.env
```

### 3. Start with Docker
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8000/api/news/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Flower Dashboard**: http://127.0.0.1:5555 (admin/bloomberg_flower)
- **Health Check**: http://127.0.0.1:8000/health/
- **API Docs**: http://127.0.0.1:8000/api/docs/

---

## 📖 Local Development

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgres://user:pass@localhost:5432/bloomberg
export REDIS_URL=redis://localhost:6379/0

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Start Celery Workers
```bash
# In separate terminal windows:

# Celery worker
celery -A config worker -l INFO

# Celery beat (scheduler)
celery -A config beat -l INFO
```

---

## 📡 API Reference

### Articles

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/articles/` | GET | List all articles |
| `/api/articles/{id}/` | GET | Get article details |
| `/api/articles/search/` | GET | Search articles |
| `/api/articles/categories/` | GET | List categories with counts |
| `/api/articles/latest/` | GET | Get latest articles |

### Search

```http
GET /api/articles/search/?q=economy&category=market&page=1
```

**Response:**
```json
{
  "total_results": 150,
  "page": 1,
  "page_size": 10,
  "total_pages": 15,
  "detected_category": "economy",
  "category_confidence": 0.87,
  "execution_time_ms": 45,
  "results": [...]
}
```

### Scraper Control

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scraper/` | GET | Get scraper status |
| `/api/scraper/toggle/` | POST | Enable/disable scraper |
| `/api/scraper/trigger/` | POST | Manually trigger scrape |
| `/api/scraper/history/` | GET | View scraping history |

### Health & Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health/` | GET | Health check endpoint |
| `/ready/` | GET | Readiness check |
| `/metrics/` | GET | Application metrics |
| `/metrics/prometheus/` | GET | Prometheus format metrics |

**Toggle Scraper:**
```http
POST /api/scraper/toggle/
Content-Type: application/json

{
  "fetch": true
}
```

---

## 🏗 Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Browser                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Nginx (Reverse Proxy)                     │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
          ┌───────────▼───────────┐ ┌─────────▼─────────┐
          │   Next.js Frontend    │ │  Django Backend   │
          │   (React, TypeScript) │ │  (REST API)       │
          └───────────────────────┘ └─────────┬─────────┘
                                              │
          ┌───────────────────────────────────┼─────────────────┐
          │                                   │                 │
          ▼                                   ▼                 ▼
┌─────────────────┐              ┌─────────────────┐   ┌────────────────┐
│   PostgreSQL    │              │     Redis       │   │  Celery Worker │
│   (Articles,    │              │  (Cache,        │   │  (Scraping,    │
│    Categories)  │              │   Broker)       │   │   AI Tasks)    │
└─────────────────┘              └─────────────────┘   └───────┬────────┘
                                                               │
                                        ┌──────────────────────┼──────────────────────┐
                                        │                      │                      │
                                        ▼                      ▼                      ▼
                             ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                             │  Celery Beat    │    │     Flower      │    │  Bloomberg RSS  │
                             │  (Scheduler)    │    │   (Monitoring)  │    │ (External Source│
                             └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow
1. **Scraping**: Celery beat triggers periodic scraping → Bloomberg RSS parsed → Articles saved
2. **Categorization**: New articles → AI categorizer → Category assigned with confidence
3. **Indexing**: Article saved → Search vector updated → Full-text index refreshed
4. **Search**: Query received → Category detected → PostgreSQL FTS → Results ranked & returned

---

## 📁 Project Structure

```
bloomberg-news-scraper/
├── backend/
│   ├── apps/
│   │   ├── news/              # News articles app
│   │   │   ├── models.py      # Article, Category models
│   │   │   ├── views.py       # API endpoints
│   │   │   ├── views_health.py # Health & metrics endpoints
│   │   │   ├── serializers.py # DRF serializers
│   │   │   ├── middleware.py  # Request correlation & monitoring
│   │   │   ├── signals.py     # Django signals
│   │   │   └── services/
│   │   │       ├── categorizer.py  # AI categorization
│   │   │       └── search.py       # Search engine
│   │   └── scraper/           # Scraper app
│   │       ├── bloomberg_scraper.py
│   │       ├── tasks.py       # Celery tasks
│   │       └── views.py       # Scraper control API
│   ├── config/                # Django settings
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API services
│   │   └── types/            # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── nginx/
│   ├── nginx.conf
│   └── conf.d/
├── docker-compose.yml
└── README.md
```

---

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Frontend Tests
```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `DEBUG` | Enable debug mode | `False` |
| `SECRET_KEY` | Django secret key | Required |
| `DATABASE_URL` | PostgreSQL connection | Required |
| `REDIS_URL` | Redis connection | Required |
| `CORS_ALLOWED_ORIGINS` | CORS whitelist | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000/api` |
| `FLOWER_USER` | Flower dashboard username | `admin` |
| `FLOWER_PASSWORD` | Flower dashboard password | `bloomberg_flower` |

---

## 📈 Performance

- **Search Response**: < 100ms average
- **Article Indexing**: Real-time with PostgreSQL triggers
- **Scraping Rate**: 100+ articles/minute with rate limiting
- **AI Categorization**: < 10ms per article (lightweight keyword-based)
- **Docker Image Size**: Optimized multi-stage builds

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Obaidulllah**

Built with ❤️ for the Technical Assessment

---

<div align="center">

**⭐ Star this repo if you found it helpful!**

</div>
