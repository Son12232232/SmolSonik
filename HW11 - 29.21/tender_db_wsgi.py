import sqlite3, html
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs
import os

DB_FILE = 'tender.db'

def ensure_db():
    # Якщо є файл, але він не читається як SQLite – видалити
    if os.path.exists(DB_FILE):
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("PRAGMA schema_version;")
            conn.close()
        except sqlite3.DatabaseError:
            os.remove(DB_FILE)

    # Далі створюємо нову БД і таблиці
    conn = sqlite3.connect(DB_FILE)
    cur  = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS suppliers (
      id      TEXT PRIMARY KEY,
      name    TEXT NOT NULL,
      rating  REAL NOT NULL,
      address TEXT
    );
    CREATE TABLE IF NOT EXISTS products (
      id   TEXT PRIMARY KEY,
      name TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS prices (
      supplier_id TEXT,
      product_id  TEXT,
      price       REAL NOT NULL,
      term        INTEGER,
      PRIMARY KEY(supplier_id,product_id)
    );
    CREATE TABLE IF NOT EXISTS coeffs (
      a1 REAL NOT NULL,
      a2 REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS tender_items (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      product_id TEXT NOT NULL,
      quantity   REAL NOT NULL
    );
    """)
    # Ініціалізуємо coeffs, якщо ще порожньо
    cur.execute("SELECT COUNT(*) FROM coeffs")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO coeffs(a1,a2) VALUES(0.5,0.5)")
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_FILE)

def get_params(env):
    if env['REQUEST_METHOD']=='GET':
        return parse_qs(env.get('QUERY_STRING',''), keep_blank_values=True)
    else:
        size = int(env.get('CONTENT_LENGTH','0') or 0)
        data = env['wsgi.input'].read(size).decode('utf-8')
        return parse_qs(data, keep_blank_values=True)

def render(body: str) -> bytes:
    page = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Тендер DB</title></head><body>"
        "<nav>"
        "<a href='/'>Головна</a> | "
        "<a href='/coeffs'>Коефіцієнти</a> | "
        "<a href='/add_item'>Додати товар</a> | "
        "<a href='/tender'>Результати</a>"
        "</nav><hr>"
        f"{body}</body></html>"
    )
    return page.encode('utf-8')

def application(env, start_response):
    ensure_db()
    path   = env.get('PATH_INFO','/')
    params = get_params(env)
    def G(k): return params.get(k, [None])[0]

    # --- Головна ---
    if path=='/':
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        body = "<h1>Тендер постачальників (SQLite)</h1>"
        return [render(body)]

    # --- Коефіцієнти ---
    if path=='/coeffs':
        conn = get_conn(); cur = conn.cursor()
        if env['REQUEST_METHOD']=='GET':
            cur.execute("SELECT a1,a2 FROM coeffs")
            a1,a2 = cur.fetchone()
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            body = f"""
            <h2>Коефіцієнти (a1+a2=1)</h2>
            <form method="post">
              a1: <input name="a1" value="{a1}" required><br>
              a2: <input name="a2" value="{a2}" required><br>
              <input type="submit" value="Зберегти">
            </form>
            """
            conn.close()
            return [render(body)]
        # POST
        try:
            a1 = float(G('a1')); a2 = float(G('a2'))
            assert abs((a1+a2)-1.0)<1e-6
            cur.execute("UPDATE coeffs SET a1=?, a2=?", (a1,a2))
            conn.commit()
            start_response("302 Found", [("Location","/coeffs")])
            return [b'']
        except:
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            return [render("<p style='color:red;'>Некоректні коефіцієнти.</p>")]

    # --- Додати товар у тендер ---
    if path=='/add_item':
        conn = get_conn(); cur = conn.cursor()
        # Завантажуємо список продуктів
        cur.execute("SELECT id,name FROM products")
        prods = cur.fetchall()
        if env['REQUEST_METHOD']=='GET':
            opts = "".join(f"<option value='{pid}'>{html.escape(name)}</option>"
                           for pid,name in prods)
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            body = f"""
            <h2>Додати товар до тендеру</h2>
            <form method="post">
              Товар: <select name="prod">{opts}</select><br>
              К-ть: <input name="qty" required><br>
              <input type="submit" value="Додати">
            </form>
            """
            conn.close()
            return [render(body)]
        # POST
        pid = G('prod'); q = G('qty')
        try:
            qty = float(q); assert pid
            cur.execute("INSERT INTO tender_items(product_id,quantity) VALUES(?,?)",
                        (pid,qty))
            conn.commit()
            start_response("302 Found",[("Location","/add_item")])
            return [b'']
        except:
            start_response("200 OK",[("Content-Type","text/html; charset=utf-8")])
            return [render("<p style='color:red;'>Невірні дані.</p>")]

    # --- Показати результати тендеру ---
    if path=='/tender':
        conn = get_conn(); cur = conn.cursor()
        # Зчитуємо дані
        cur.execute("SELECT a1,a2 FROM coeffs"); a1,a2 = cur.fetchone()
        cur.execute("SELECT id,name,rating FROM suppliers")
        sups = cur.fetchall()
        cur.execute("SELECT supplier_id,product_id,price FROM prices")
        prs = cur.fetchall()
        cur.execute("SELECT id,name FROM products")
        prds = cur.fetchall()
        cur.execute("SELECT product_id,quantity FROM tender_items")
        items = cur.fetchall()
        conn.close()

        # Знаходимо Pmax та Rmax
        from collections import defaultdict
        Pmax = defaultdict(float)
        for sid,pid,price in prs:
            Pmax[pid] = max(Pmax[pid], price)
        Rmax = max(r for _,_,r in sups) if sups else 1.0

        # Формуємо рядки таблиці
        rows = ""
        for pid,qty in items:
            # кандидати для pid
            cands = [(sid,price) for sid,pid2,price in prs if pid2==pid]
            best = None; bestS = -1
            for sid, price in cands:
                rating = next(r for sid2,_,r in sups if sid2==sid)
                S = a1*(price/Pmax[pid]) + a2*(rating/Rmax)
                if S>bestS:
                    bestS, best = S,(sid,price)
            sup_name = next(n for sid2,n,_ in sups if sid2==best[0])
            prod_name= next(n for pid2,n in prds if pid2==pid)
            cost = best[1]*qty
            rows += (
                f"<tr>"
                f"<td>{html.escape(prod_name)}</td>"
                f"<td>{qty:.2f}</td>"
                f"<td>{html.escape(sup_name)}</td>"
                f"<td>{best[1]:.2f}</td>"
                f"<td>{cost:.2f}</td>"
                "</tr>"
            )

        start_response("200 OK",[("Content-Type","text/html; charset=utf-8")])
        body = f"""
        <h2>Результати тендеру</h2>
        <table border="1" cellpadding="4">
          <tr><th>Товар</th><th>К-ть</th><th>Постачальник</th>
              <th>Ціна</th><th>Вартість</th></tr>
          {rows}
        </table>
        """
        return [render(body)]

    # --- 404 ---
    start_response("404 NOT FOUND",[("Content-Type","text/plain; charset=utf-8")])
    return [b"404 Not Found"]

if __name__=='__main__':
    print("WSGI-сервер запущено на http://localhost:8051/")
    make_server('',8051,application).serve_forever()
