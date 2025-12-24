# Smart Fridge – minimal DB + Python integration

## 1) Install
```bash
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

## 2)Database Requirement

This project uses a local MySQL database via XAMPP.

- XAMPP MySQL **must be running**
- Port: **3306**
- Host: `localhost`
- User: `root`
- Password: *(empty)*

> ⚠️ If MySQL is not running, the application will fail to start.
> Make sure MySQL is green in the XAMPP Control Panel.

