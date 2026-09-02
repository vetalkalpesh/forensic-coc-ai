"""
dataset_generator/generators/base_generator.py
Shared base class providing seeded Faker instance, DB connection, and utilities.
All synthetic data generators inherit from this class.
"""
import random
import hashlib
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
import mysql.connector
from config import DB_CONFIG, SYNTHETIC_HEADER


class BaseGenerator:
    """Base class for all dataset generators. Provides seeded Faker, DB connection, utilities."""

    def __init__(self, seed: int = 42, db_config: dict = None, dry_run: bool = False):
        self.seed     = seed
        self.dry_run  = dry_run
        self.db_cfg   = db_config or DB_CONFIG

        # Seeded Faker — deterministic names/addresses/etc
        self.fake = Faker("en_IN")    # Indian locale for realistic names/places
        Faker.seed(seed)
        random.seed(seed)

        # DB connection (None in dry-run mode)
        self._conn = None
        self._cur  = None

    # ── DB Connection ────────────────────────────────────────
    def connect(self):
        if self.dry_run:
            return
        import os
        try:
            import dotenv
            # Try loading .env from workspace root and relative paths
            root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
            if os.path.exists(root_env):
                dotenv.load_dotenv(root_env)
            dotenv.load_dotenv()
        except Exception:
            pass
        cfg = dict(self.db_cfg)
        env_pwd = os.environ.get("DB_PASSWORD")
        if env_pwd is not None:
            cfg["password"] = env_pwd
        self._conn = mysql.connector.connect(**cfg)
        self._cur  = self._conn.cursor(dictionary=True)

    def disconnect(self):
        if self._cur:
            self._cur.close()
        if self._conn:
            self._conn.commit()
            self._conn.close()

    def execute(self, sql: str, params: tuple = None) -> int:
        """Execute a write statement. Returns last insert ID."""
        if self.dry_run:
            return 0
        self._cur.execute(sql, params or ())
        self._conn.commit()
        return self._cur.lastrowid

    def execute_many(self, sql: str, param_list: list):
        """Bulk insert. Faster than individual executes."""
        if self.dry_run or not param_list:
            return
        self._cur.executemany(sql, param_list)
        self._conn.commit()

    def query(self, sql: str, params: tuple = None) -> list:
        """Execute a SELECT and return all rows."""
        if self.dry_run:
            return []
        self._cur.execute(sql, params or ())
        return self._cur.fetchall()

    def query_one(self, sql: str, params: tuple = None) -> dict:
        """Execute a SELECT and return first row."""
        if self.dry_run:
            return {}
        self._cur.execute(sql, params or ())
        return self._cur.fetchone()

    # ── Utilities ────────────────────────────────────────────
    def sha256(self, content: str) -> str:
        """Compute SHA-256 hash of a string."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def sha256_bytes(self, data: bytes) -> str:
        """Compute SHA-256 hash of bytes."""
        return hashlib.sha256(data).hexdigest()

    def weighted_choice(self, weights_dict: dict):
        """Choose a key from dict by weight values."""
        keys   = list(weights_dict.keys())
        values = list(weights_dict.values())
        return random.choices(keys, weights=values, k=1)[0]

    def poisson_int(self, lam: float, min_val: int = 1, max_val: int = None) -> int:
        """Sample from Poisson distribution, clamped."""
        import math
        # Simple Poisson via inverse transform (small lambda only)
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.random()
        val = max(min_val, k - 1)
        if max_val is not None:
            val = min(val, max_val)
        return val

    def synthetic_header(self) -> str:
        return SYNTHETIC_HEADER

    def date_between(self, start_year: int, end_year: int):
        """Generate a random date between two years."""
        from datetime import date
        start = date(start_year, 1, 1)
        end   = date(end_year,  12, 31)
        delta = (end - start).days
        return start.replace(day=1) + __import__("datetime").timedelta(days=random.randint(0, delta))

    def datetime_between(self, start_dt, end_dt):
        """Generate random datetime between two datetimes."""
        from datetime import datetime, timedelta
        if isinstance(start_dt, str):
            start_dt = datetime.fromisoformat(start_dt)
        if isinstance(end_dt, str):
            end_dt   = datetime.fromisoformat(end_dt)
        delta = (end_dt - start_dt).total_seconds()
        return start_dt + __import__("datetime").timedelta(seconds=random.randint(0, int(delta)))

    def print_progress(self, label: str, done: int, total: int):
        pct = int(100 * done / max(total, 1))
        bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
        print(f"\r  {label:30s} [{bar}] {done}/{total}", end="", flush=True)
        if done >= total:
            print()
