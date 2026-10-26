# ReliefLine

Relief-goods monitoring and food-pack demand forecasting for the Pangasinan
PSWDO, the CSWDO/MSWDO offices of Urdaneta City, Santa Barbara and Calasiao,
and their barangays. Flask + MySQL/MariaDB.

## Project layout

```
reliefline/
├── run.py                 # development server
├── wsgi.py                # production WSGI entry point (loaded by the host)
├── requirements.txt
├── app/
│   ├── __init__.py        # create_app(): config, blueprints, context processors
│   ├── config.py          # every setting, read from the environment
│   ├── extensions.py      # SQLAlchemy + Flask-Login instances
│   ├── models/            # ORM models (one module per table group)
│   ├── routes/            # blueprints: auth, admin, pswdo, cswdo, barangay,
│   │                      #   prediction, reports, receipts
│   ├── ml/                # two-stage food-pack forecaster + trained artifact
│   ├── utils/             # shared helpers (time zone, roles, weather, mail…)
│   ├── templates/         # Jinja templates, one folder per role
│   └── static/            # css, js, img, geo; uploads/ is runtime data
├── database/
│   └── reliefline_db.sql  # full schema + data (incl. the real relief records)
└── scripts/
    ├── train_model.py          # retrain the forecaster
    ├── check_forecast.py       # forecaster smoke checks
    ├── gen_dark_css.py         # regenerate dark-mode CSS after CSS edits
    └── sync_db_dump.sh         # re-dump database/reliefline_db.sql
```

## Local development

```bash
cd reliefline
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # Linux/macOS: .venv/bin/pip
# create .env with SECRET_KEY, DATABASE_URL and FLASK_DEBUG=1 (see app/config.py)
mysql -u root -e "CREATE DATABASE reliefline_db"
mysql -u root reliefline_db < database/reliefline_db.sql
.venv/Scripts/python run.py
```

## Deployment

1. **Database** – create a MySQL 8 / MariaDB database and a dedicated user,
   then load `reliefline/database/reliefline_db.sql`.
2. **Environment** – set these variables in `reliefline/.env` on the server:
   - `SECRET_KEY` – long random value (the app will not start without it).
   - `DATABASE_URL` – points at the production database.
   - `FLASK_DEBUG=0`.
   - `SESSION_COOKIE_SECURE=1` once served over HTTPS.
   - `BEHIND_PROXY=1` when the host sits in front of the app (most hosts do).
   - `MAIL_*` – optional, for password-reset emails.
3. **Install** – `pip install -r requirements.txt` in a virtualenv.
4. **Run** – point the host's WSGI setup at `reliefline/wsgi.py` (it exposes `app`),
   and let the host serve `reliefline/app/static/` directly if possible.
5. **Persistent files** – `app/static/uploads/` holds user-uploaded proof
   photos and attachments. Keep it on persistent storage and back it up
   together with the database.

The whole system runs on Philippine time (UTC+8) regardless of the server's
time zone; see `app/utils/timezone.py`.
