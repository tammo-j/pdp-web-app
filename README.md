PDP Web Application for information and preordering system
----------------------------------------------------------

1.	The application includes a Django project `manage.py` & `backend/`
	and a Django application `orders/`. These are responsible for the
	database and REST/JSON interface to the database.

2.	The `ui/` Django application serves the templates required.
	The UI is built on jQuery mobile and javascript which
	are located in `www/`.

3.	The `raspberry/` includes installation instruction and stand
	alone code (not Django) for Raspberry Pi card computer to
	direct a Dymo Labelwriter 4xx ticket printer.
