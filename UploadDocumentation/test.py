import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path
from urllib.parse import urlparse, unquote

# Load environment variables from the repository root .env
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# Use DATABASE_URL from env for a single source of truth
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
	print("ERROR: DATABASE_URL is not set in the repository root .env")
	raise SystemExit(2)

# Show sanitized connection info (do not print the password)
parsed = urlparse(DATABASE_URL)
user = unquote(parsed.username) if parsed.username else None
host = parsed.hostname
port = parsed.port
dbname = parsed.path.lstrip('/') if parsed.path else None
print(f"Using DB host={host} port={port} dbname={dbname} user={user}")

try:
	conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
	print("Connected to the database successfully (original DATABASE_URL)")
	conn.close()
except Exception as e:
	print("Connection failed:", type(e).__name__, str(e))
	# Try alternate username variant: strip suffix after first dot
	parsed_pw = unquote(parsed.password) if parsed.password else None
	if parsed_pw:
		alt_user = user.split('.')[0] if user and '.' in user else user
		if alt_user and alt_user != user:
			alt_netloc = f"{alt_user}:{parsed_pw}@{host}:{port}/{dbname}"
			alt_dsn = f"postgresql://{alt_netloc}"
			print(f"Trying alternate username '{alt_user}' with same password...")
			try:
				conn2 = psycopg2.connect(alt_dsn, connect_timeout=10)
				print("Connected successfully with alternate username")
				conn2.close()
			except Exception as e2:
				print("Alternate connect failed:", type(e2).__name__, str(e2))
	raise