
import os, json, html
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs
from datetime import datetime

EMP_FILE    = 'employees.json'
TS_FILE     = 'timesheets.json'

def load(fname):
    if os.path.exists(fname):
        with open(fname, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save(fname, data):
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def render(body: str) -> bytes:
    page = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Табель і ЗП</title></head><body>"
        "<nav>"
          "<a href='/employees'>Співробітники</a> | "
          "<a href='/timesheet'>Табель</a> | "
          "<a href='/payroll'>Розрахунок ЗП</a>"
        "</nav><hr>"
        f"{body}"
        "</body></html>"
    )
    return page.encode('utf-8')

def get_params(env):
    if env['REQUEST_METHOD']=='GET':
        qs = env.get('QUERY_STRING','')
        return parse_qs(qs, keep_blank_values=True)
    else:
        try:
            l = int(env.get('CONTENT_LENGTH','0') or 0)
        except:
            l = 0
        data = env['wsgi.input'].read(l).decode('utf-8')
        return parse_qs(data, keep_blank_values=True)

def application(env, start_response):
    path   = env.get('PATH_INFO','/')
    params = get_params(env)
    def G(k):
        v = params.get(k)
        return v[0] if v else None

    # --- ГОЛОВНА ---
    if path=='/':
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        b = "<h1>Табель і розрахунок ЗП</h1>"
        b += "<ul>"
        b += "<li><a href='/employees'>Управління співробітниками</a></li>"
        b += "<li><a href='/timesheet'>Ввести табель</a></li>"
        b += "<li><a href='/payroll'>Розрахувати ЗП</a></li>"
        b += "</ul>"
        return [render(b)]

    # --- СПІВРОБІТНИКИ ---
    if path=='/employees':
        emps = load(EMP_FILE)
        # POST — додаємо нового
        if env['REQUEST_METHOD']=='POST':
            name = G('name')
            byear= G('byear')
            try:
                bi  = int(byear); assert name
            except:
                msg = "<p style='color:red;'>Помилка даних.</p>"
                start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
                return [render(msg)]
            new_id = max((e['id'] for e in emps), default=0)+1
            emps.append({'id':new_id,'name':name,'byear':bi})
            save(EMP_FILE, emps)
            return [render(f"<p>Додано {html.escape(name)} (ID={new_id})</p>")]

        # GET — список + форма
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        b = "<h2>Список співробітників</h2><ul>"
        for e in emps:
            b += f"<li>ID {e['id']}: {html.escape(e['name'])}, рік {e['byear']}</li>"
        b += "</ul><h3>Додати співробітника</h3>"
        b += ("<form method='post'>"
              "Прізвище: <input name='name' required><br>"
              "Рік народження: <input name='byear' type='number' required><br>"
              "<input type='submit' value='Додати'></form>")
        return [render(b)]

    # --- ТАБЕЛЬ ---
    if path=='/timesheet':
        emps = load(EMP_FILE)
        sheets = load(TS_FILE)
        # POST — зберегти табель
        if env['REQUEST_METHOD']=='POST':
            eid    = G('emp_id')
            month  = G('month')    # формат YYYY-MM
            raw    = G('entries')  # в textarea
            try:
                i_emp = int(eid)
                datetime.strptime(month, "%Y-%m")
                # розбираємо рядки
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                recs = []
                for ln in lines:
                    date_str, hrs = ln.split(':')
                    d = datetime.fromisoformat(date_str).date()
                    h = float(hrs)
                    recs.append({'date':d.isoformat(),'hours':h})
            except Exception:
                return [render("<p style='color:red;'>Невірний формат табеля.</p>")]
            new_id = max((s['id'] for s in sheets), default=0)+1
            sheets.append({
                'id': new_id,
                'emp_id': i_emp,
                'month': month,
                'records': recs
            })
            save(TS_FILE, sheets)
            return [render(f"<p>Табель збережено (ID={new_id}).</p>")]

        # GET — форма введення табеля
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        opts = "".join(f"<option value='{e['id']}'>{html.escape(e['name'])}</option>" for e in emps)
        b = ("<h2>Ввести табель співробітника</h2>"
             "<form method='post'>"
             "Співробітник: <select name='emp_id'>" + opts + "</select><br>"
             "Місяць (YYYY-MM): <input name='month' required><br>"
             "Табель (рядки у форматі YYYY-MM-DD:години):<br>"
             "<textarea name='entries' rows='8' cols='30'></textarea><br>"
             "<input type='submit' value='Зберегти'></form>")
        return [render(b)]

    # --- РОЗРАХУНОК ЗП ---
    if path=='/payroll':
        emps = load(EMP_FILE)
        sheets = load(TS_FILE)
        # POST — розрахувати за обраний місяць
        if env['REQUEST_METHOD']=='POST':
            month = G('month')
            try:
                datetime.strptime(month, "%Y-%m")
            except:
                return [render("<p style='color:red;'>Невірний формат місяця.</p>")]
            # для кожного співробітника підсумуємо години та ZP = sum(hours)*rate_per_hour
            # тут беремо ставку як константу, скажімо 50₴/год
            RATE = 50.0
            b = f"<h2>Розрахунок ЗП за {month}</h2>"
            b += ("<table border='1' cellpadding='4'>"
                  "<tr><th>Працівник</th><th>Годин</th><th>Плата, ₴</th></tr>")
            for e in emps:
                total_h = sum(
                    rec['hours']
                    for s in sheets
                    if s['emp_id']==e['id'] and s['month']==month
                    for rec in s['records']
                )
                pay = total_h * RATE
                b += ("<tr>"
                      f"<td>{html.escape(e['name'])}</td>"
                      f"<td>{total_h:.2f}</td>"
                      f"<td>{pay:.2f}</td>"
                      "</tr>")
            b += "</table>"
            return [render(b)]

        # GET — вибір місяця
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        b = ("<h2>Розрахувати ЗП усіх співробітників</h2>"
             "<form method='post'>"
             "Місяць (YYYY-MM): <input name='month' required><br>"
             "<input type='submit' value='Розрахувати'></form>")
        return [render(b)]

    # --- 404 ---
    start_response("404 NOT FOUND", [("Content-Type","text/plain; charset=utf-8")])
    return [b"404 Not Found"]

if __name__=='__main__':
    print("WSGI-сервер запущено на http://localhost:8051/")
    with make_server('',8051,application) as srv:
        srv.serve_forever()
