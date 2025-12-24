# Smart Fridge – Python, MySQL, and LLM Integration

A local Python application that simulates a smart fridge system by combining:
- Computer vision (food classification)
- A MySQL database (inventory & shelf-life tracking)
- An LLM (Google Gemini) for recipe generation

The application is designed for **local development and academic use**.

---

## Features

- Automatic database schema creation
- Food item tracking with expiration status
- Support for fridge vs freezer storage
- Recipe generation using an LLM based on available items
- Safe, repeatable startup (idempotent schema initialization)

---

## System Requirements

- Python 3.10+
- XAMPP (MySQL only)
- Windows / macOS / Linux

---

## Installation

### Prerequisites

- Python 3.10 or newer
- XAMPP (MySQL)
- Git (optional)

### Clone the repository

```bash
git clone https://github.com/dany439/smart_fridge.git
cd smart_fridge
```
### Create and activate a virtual environment

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

### Install dependencies

pip install -r requirements.txt

### Configure environment variables

Create a .env file in the project root and add:

```
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=smart_fridge

GEMINI_API_KEY=your_api_key_here
```

---

### Supported Food Classes

The classifier currently supports the following food items:

- pizza
- sushi
- hamburger
- french fries
- spaghetti bolognese
- fried rice
- chicken wings
- caesar salad
- steak
- ice cream

