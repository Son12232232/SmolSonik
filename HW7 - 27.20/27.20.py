# vector_pay_wsgi.py
import json, os
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs
import html
from datetime import datetime

DRIVERS_FILE = 'drivers.json'
SHEETS_FILE = 'sheets.json'

def load_json(fname):
    if os.path.exists(fname):
        with open(fname, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(fname, data):
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def render(body: str) -> bytes:
    page = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Оплата перевезень</title></head><body>"
        "<nav>"
        "<a href='/'>Головна</a> | "
        "<a href='/add_driver'>Додати водія</a> | "
        "<a href='/add_sheet'>Додати маршрутний лист</a> | "
        "<a href='/calc'>Розрахувати плату</a>"
        "</nav><hr>"
        f"{body}"
        "</body></html>"
    )
    return page.encode('utf-8')

def parse_params(environ):
    if environ['REQUEST_METHOD'] == 'GET':
        qs = environ.get('QUERY_STRING','')
        return parse_qs(qs, keep_blank_values=True)
    else:
        try:
            length = int(environ.get('CONTENT_LENGTH','0') or 0)
        except:
            length = 0
        body = environ['wsgi.input'].read(length).decode('utf-8')
        return parse_qs(body, keep_blank_values=True)

def application(environ, start_response):
    path = environ.get('PATH_INFO','/')
    params = parse_params(environ)
    def g(key):
        v = params.get(key)
        return v[0] if v else None

    # --- Головна сторінка ---
    if path == '/':
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        body = """
        <h1>Оплата за перевезення</h1>
        <ul>
          <li><a href="/add_driver">Додати водія</a></li>
          <li><a href="/add_sheet">Додати маршрутний лист</a></li>
          <li><a href="/calc">Розрахувати плату</a></li>
        </ul>
        """
        return [render(body)]

    # --- Додати водія ---
    if path == '/add_driver':
        # GET – показати форму
        if environ['REQUEST_METHOD'] == 'GET':
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            body = """
            <h2>Додати нового водія</h2>
            <form method="post">
              Прізвище: <input name="name" required><br>
              Рік народження: <input name="byear" type="number" required><br>
              Ставка (₴ за тонно·км): <input name="rate" required><br>
              Вантажопідйомність (тонн): <input name="capacity" required><br>
              <input type="submit" value="Зберегти">
            </form>
            """
            return [render(body)]
        # POST – зберегти
        name     = g('name')
        byear    = g('byear')
        rate     = g('rate')
        capacity = g('capacity')
        try:
            byear_i = int(byear)
            rate_f  = float(rate)
            cap_f   = float(capacity)
            assert name
        except:
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            return [render("<p style='color:red;'>Невірні дані. Спробуйте ще.</p>")]
        drivers = load_json(DRIVERS_FILE)
        new_id = max((d['id'] for d in drivers), default=0) + 1
        drivers.append({
            'id': new_id,
            'name': name,
            'byear': byear_i,
            'rate': rate_f,
            'capacity': cap_f
        })
        save_json(DRIVERS_FILE, drivers)
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        return [render(f"<p>Водія <b>{html.escape(name)}</b> додано (ID={new_id}).</p>")]

    # --- Додати маршрутний лист ---
    if path == '/add_sheet':
        drivers = load_json(DRIVERS_FILE)
        # GET – форма
        if environ['REQUEST_METHOD'] == 'GET':
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            opts = ''.join(f"<option value='{d['id']}'>{html.escape(d['name'])}</option>" for d in drivers)
            body = f"""
            <h2>Додати маршрутний лист</h2>
            <form method="post">
              Водій: <select name="driver_id">{opts}</select><br>
              Дата (YYYY-MM-DD): <input name="date" required><br>
              Тонно·км: <input name="tonkm" required><br>
              <input type="submit" value="Зберегти">
            </form>
            """
            return [render(body)]
        # POST – зберегти
        try:
            did   = int(g('driver_id'))
            date  = datetime.fromisoformat(g('date')).date().isoformat()
            tonkm = float(g('tonkm'))
        except:
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            return [render("<p style='color:red;'>Невірні дані маршрутного листа.</p>")]
        sheets = load_json(SHEETS_FILE)
        new_id = max((s['id'] for s in sheets), default=0) + 1
        sheets.append({
            'id': new_id,
            'driver_id': did,
            'date': date,
            'tonkm': tonkm
        })
        save_json(SHEETS_FILE, sheets)
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        return [render(f"<p>Лист додано для водія ID={did} на {date}.</p>")]

    # --- Розрахувати плату ---
    if path == '/calc':
        drivers = load_json(DRIVERS_FILE)
        sheets  = load_json(SHEETS_FILE)
        # GET – форма вибору
        if environ['REQUEST_METHOD'] == 'GET':
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            opts = ''.join(f"<option value='{d['id']}'>{html.escape(d['name'])}</option>" for d in drivers)
            body = f"""
            <h2>Розрахунок заробітку водія за період</h2>
            <form method="post">
              Водій: <select name="driver_id">{opts}</select><br>
              Дата з: <input name="from" placeholder="YYYY-MM-DD" required><br>
              Дата по: <input name="to"   placeholder="YYYY-MM-DD" required><br>
              <input type="submit" value="Розрахувати">
            </form>
            """
            return [render(body)]
        # POST – обчислити
        try:
            did  = int(g('driver_id'))
            d0   = datetime.fromisoformat(g('from')).date()
            d1   = datetime.fromisoformat(g('to')).date()
            assert d0 <= d1
        except:
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            return [render("<p style='color:red;'>Невірні дати або водій.</p>")]
        drv = next((d for d in drivers if d['id']==did), None)
        if not drv:
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            return [render("<p style='color:red;'>Водій не знайдений.</p>")]
        # Фільтруємо маршрутні листи
        total = 0.0
        rows = []
        for s in sheets:
            if s['driver_id']==did:
                dt = datetime.fromisoformat(s['date']).date()
                if d0 <= dt <= d1:
                    pay = s['tonkm'] * drv['rate']
                    total += pay
                    rows.append((s['date'], s['tonkm'], pay))
        # Формуємо результат
        lines = "".join(f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]:.2f}</td></tr>" for r in rows)
        body = f"""
        <h2>Звіт для {html.escape(drv['name'])} за {d0} — {d1}</h2>
        <table border="1" cellpadding="5">
          <tr><th>Дата</th><th>Тонно·км</th><th>Плата, ₴</th></tr>
          {lines}
          <tr><td colspan="2"><b>Разом</b></td><td><b>{total:.2f}</b></td></tr>
        </table>
        """
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        return [render(body)]

    # --- Якщо шлях невідомий ---
    start_response("404 NOT FOUND", [("Content-Type","text/plain; charset=utf-8")])
    return [b"404 Not Found"]

if __name__ == '__main__':
    print("Запуск WSGI-сервера на http://localhost:8051/")
    with make_server('', 8051, application) as srv:
        srv.serve_forever()
