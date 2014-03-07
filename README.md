pdp-web-app
===========

PDP Web Application for information and preordering system

***

The application includes a Django project `manage.py` & `backend/`
and a Django application `orders/`. These are responsible for the
database and REST/JSON interface to the database.

The `www/` directory holds the static WWW user interface (UI)
implementation which depends on the URL:s for the backend.
The UI is based on jQuery mobile.
