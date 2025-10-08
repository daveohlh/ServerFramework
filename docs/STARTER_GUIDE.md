# Tech Stack

- [sesh.fyi timestamp tool](https://sesh.fyi/timestamp/) – sync your time across timezones  
- **Python** – backend development  
- **TypeScript** – scripting/frontend logic  
- **Docker** – containerization  
- **Obsidian** – internal documentation and knowledge management  

# Quick Start && Requirements

### Clone the repo:

    git clone https://github.com/JamesonRGrieve/ServerFramework.git

### Basic Operations
- **Start the application**: `python src/app.py` (handles virtual environment setup automatically)
- **Run tests**: `pytest` (use specific test markers for targeted testing)
- **Format code**: `black src/` (configured with 88-character line length)
- **Type checking**: `mypy src/` (if available in dev dependencies)

### How to find docs

There is this obsidian vault with an extension that hides empty folders pre-installed, so the layer specific docs are easy to find and are formatted nicely.

# Backend Architecture and Idioms

This is a **FastAPI-based server framework** with a layered architecture designed for scalability and modularity. The codebase follows strict separation of concerns with an extension-based plugin system.

## System Architecture Layers
As previous mentioned each of then have a Documentation file inside their folder that you can easily see with obsidian but also with the IDE of choice
1. **Database Layer (DB_*.py)**: SQLAlchemy ORM models with declarative base
2. **Business Logic Layer (BLL_*.py)**: Core business logic managers with CRUD operations
3. **Endpoint Layer (EP_*.py)**: FastAPI router implementations with automatic CRUD endpoint generation
4. **Extensions (EXT_*.py)**: Plugin system for adding modular functionality
5. **Providers (PRV_*.py)**: Standardized interfaces to external services

## Key Architectural Patterns

- **RORO Pattern**: All methods follow "Receive Object, Return Object" pattern
- **Hook System**: Comprehensive before/after hook support for all BLL operations
- **Model Registry**: Centralized Pydantic model management with automatic SQLAlchemy binding
- **Mixin System**: Common behaviors like `DatabaseMixin`, `RouterMixin`, `RotationMixin`, and `ApplicationModel` are used to extend logic, add CRUD operations, and connect models to the core runtime without inheritance bloat.
- **Registry Pattern**: Static registries (e.g. `ExtensionRegistry`, `ModelRegistry`) are used to auto-discover and coordinate classes, avoiding manual wiring and enabling loose coupling with high discoverability.

## Files Naming Convention

| Prefix   | Meaning                 |
| -------- | ----------------------- |
| `DB_`    | Database models         |
| `BLL_`   | Business Logic managers |
| `EP_`    | API Endpoints           |
| `EXT_`   | Extensions modules      |
| `PRV_`   | Providers interfaces    |
| `SVC_`   | Services                |
| `SYS_`   | System                  |
| `PIP_`   | pip dependency          |
| `*_test` | tests                   |

# Endpoints

- **GraphQL**: http://localhost:1996/graphql  
- **REST Docs**: http://localhost:1996/docs#/  
- **Local LLM Gateway**: https://llm.zephyrex.dev/

# Git Workflow

Start a new feature branch from `dev`:

    git checkout dev
    git pull origin dev
    git checkout -b feat/your-feature-name

Commit and push:

    git commit -m "Clear commit message"
    git push origin feat/your-feature-name

# CI/CD

**TODO**:  
- GitHub Actions 
- Automate testing, linting, and deployment  

# Tests
**TODO**
