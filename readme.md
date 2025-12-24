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

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate



pip install -r requirements.txt
