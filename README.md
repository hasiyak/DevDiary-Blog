# DevDiary - Modern Full-Stack Blog CMS

DevDiary is a lightweight and responsive blog CMS built with **Flask** and **SQLite**.

## Features

- Secure admin authentication
- Full CRUD for blog posts
- Rich text editing in admin forms (CKEditor 5)
- AJAX newsletter subscription endpoint
- Modern responsive UI (Bootstrap 5)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run
```

The app creates its SQLite database automatically in `instance/devdiary.db`.

Default admin login (override with env vars `ADMIN_USERNAME` / `ADMIN_PASSWORD`):

- Username: `admin`
- Password: `admin123`

## Tests

```bash
python -m unittest discover -s tests
```