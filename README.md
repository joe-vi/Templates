# Code Templates

A collection of production-ready templates for various frameworks and architectures. Each template is fully functional, opinionated, and ready to use as a starting point for real projects.

## Templates

### FastAPI

| Template | Description |
|----------|-------------|
| [FastAPI Clean Architecture + PostgreSQL](FastAPI/API_PostgressDB/README.md) | Full-stack FastAPI backend with Clean Architecture, async PostgreSQL, JWT auth, and dependency injection |

---

## How to Use a Template

Each template has its own `README.md` with full setup instructions, including steps to download just that template without cloning the entire repo.

---

## Structure

```
Templates/
└── FastAPI/
    └── API_PostgressDB/    # FastAPI + Clean Architecture + PostgreSQL
```

---

## Contributing

When adding a new template:

1. Place it under a folder named after the framework or category (e.g. `FastAPI/`, `NestJS/`, `Django/`)
2. Include a `README.md` inside the template with setup instructions and a download one-liner
3. Add an entry to the table above with a link to that README