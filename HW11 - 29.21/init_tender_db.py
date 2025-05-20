# init_tender_db.py
import sqlite3
from pathlib import Path

DB_FILE = 'tender.db'

# Якщо є стара БД — видалимо, щоб стартувати з чистого аркуша
if Path(DB_FILE).exists():
    Path(DB_FILE).unlink()

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# 1) Створюємо таблиці
cur.executescript("""
CREATE TABLE suppliers (
  id      TEXT PRIMARY KEY,
  name    TEXT NOT NULL,
  rating  REAL NOT NULL,
  address TEXT
);

CREATE TABLE products (
  id   TEXT PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE prices (
  supplier_id TEXT,
  product_id  TEXT,
  price       REAL NOT NULL,
  term        INTEGER,
  PRIMARY KEY(supplier_id,product_id),
  FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
  FOREIGN KEY(product_id)  REFERENCES products(id)
);

CREATE TABLE coeffs (
  a1 REAL NOT NULL,
  a2 REAL NOT NULL
);

CREATE TABLE tender_items (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id TEXT NOT NULL,
  quantity   REAL NOT NULL,
  FOREIGN KEY(product_id) REFERENCES products(id)
);
""")

# 2) Вставляємо початкові записи згідно з умовою
suppliers = [
    ('S01','Доміно',4,'domino@com.ua'),
    ('S02','Кондор',6,'condor@com.ua'),
]
cur.executemany(
    "INSERT INTO suppliers(id,name,rating,address) VALUES (?,?,?,?)",
    suppliers
)

products = [
    ('P01','Олівець'),
    ('P02','Ручка кулькова'),
]
cur.executemany(
    "INSERT INTO products(id,name) VALUES (?,?)",
    products
)

prices = [
    ('S01','P01',2.5,5),
    ('S02','P01',2.4,6),
]
cur.executemany(
    "INSERT INTO prices(supplier_id,product_id,price,term) VALUES (?,?,?,?)",
    prices
)

# 3) Ініціалізуємо коефіцієнти a1,a2 (за замовчуванням 0.5 і 0.5)
cur.execute("INSERT INTO coeffs(a1,a2) VALUES (0.5,0.5)")

conn.commit()
conn.close()

print("✅ tender.db створено та заповнено початковими даними.")
