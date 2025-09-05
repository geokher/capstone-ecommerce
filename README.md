# Capstone Project: E-commerce Store API

## Overview

This is a Flask-based e-commerce API for managing users, products, carts, and orders. It includes:

* User registration and login (JWT authentication)
* Admin-only product creation
* Public product listing
* Add products to cart
* Checkout and order creation

Setup Instructions

1. Clone the repository

2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create the database

```python
from app import db, app
with app.app_context():
    db.create_all()
```

5. Run the app

```bash
python app.py
```

The API will be accessible at http://127.0.0.1:5000/.
