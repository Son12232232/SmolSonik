import os
import html
import xml.etree.ElementTree as ET
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs

SUP_FILE     = 'suppliers.xml'
PROD_FILE    = 'products.xml'
PRICE_FILE   = 'prices.xml'
TENDER_FILE  = 'tender.xml'
COEFFS_FILE  = 'coeffs.xml'

def ensure_files():
    # Створюємо tender.xml та coeffs.xml, якщо їх нема
    if not os.path.exists(TENDER_FILE):
        root = ET.Element('tender')
        ET.ElementTree(root).write(TENDER_FILE, encoding='utf-8', xml_declaration=True)
    if not os.path.exists(COEFFS_FILE):
        root = ET.Element('coeffs')
        ET.SubElement(root, 'a1').text = '0.5'
        ET.SubElement(root, 'a2').text = '0.5'
        ET.ElementTree(root).write(COEFFS_FILE, encoding='utf-8', xml_declaration=True)

def load_suppliers():
    tree = ET.parse(SUP_FILE)
    out = []
    for s in tree.getroot().findall('supplier'):
        out.append({
            'id':      s.get('id'),
            'name':    s.findtext('name'),
            'rating':  float(s.findtext('rating')),
            'address': s.findtext('address')
        })
    return out

def load_products():
    tree = ET.parse(PROD_FILE)
    out = []
    for p in tree.getroot().findall('product'):
        out.append({'id': p.get('id'), 'name': p.findtext('name')})
    return out

def load_prices():
    tree = ET.parse(PRICE_FILE)
    out = []
    for pr in tree.getroot().findall('price'):
        out.append({
            'supplier': pr.findtext('supplier'),
            'product':  pr.findtext('product'),
            'price':    float(pr.findtext('price')),
            'term':     int(pr.findtext('term'))
        })
    return out

def load_tender():
    tree = ET.parse(TENDER_FILE)
    out = []
    for it in tree.getroot().findall('item'):
        out.append({
            'product':  it.get('product'),
            'quantity': float(it.get('quantity'))
        })
    return out

def save_tender(items):
    root = ET.Element('tender')
    for it in items:
        ET.SubElement(root, 'item', product=it['product'], quantity=str(it['quantity']))
    ET.ElementTree(root).write(TENDER_FILE, encoding='utf-8', xml_declaration=True)

def load_coeffs():
    tree = ET.parse(COEFFS_FILE)
    r = tree.getroot()
    return float(r.findtext('a1')), float(r.findtext('a2'))

def save_coeffs(a1, a2):
    root = ET.Element('coeffs')
    ET.SubElement(root, 'a1').text = str(a1)
    ET.SubElement(root, 'a2').text = str(a2)
    ET.ElementTree(root).write(COEFFS_FILE, encoding='utf-8', xml_declaration=True)

def render(body: str) -> bytes:
    html_page = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Тендер постачальників</title></head><body>"
        "<nav>"
        "<a href='/'>Головна</a> | "
        "<a href='/coeffs'>Коефіцієнти</a> | "
        "<a href='/add_item'>Додати товар</a> | "
        "<a href='/tender'>Показати тендер</a>"
        "</nav><hr>"
        f"{body}</body></html>"
    )
    return html_page.encode("utf-8")

def get_params(env):
    if env['REQUEST_METHOD'] == 'GET':
        return parse_qs(env.get('QUERY_STRING',''), keep_blank_values=True)
    else:
        length = int(env.get('CONTENT_LENGTH','0') or 0)
        data = env['wsgi.input'].read(length).decode('utf-8')
        return parse_qs(data, keep_blank_values=True)

def application(env, start_response):
    ensure_files()
    path   = env.get('PATH_INFO','/')
    params = get_params(env)
    def G(key): return params.get(key, [None])[0]

    # --- Головна ---
    if path == '/':
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        body = "<h1>Тендер постачальників</h1>"
        return [render(body)]

    # --- Налаштування коефіцієнтів ---
    if path == '/coeffs':
        if env['REQUEST_METHOD'] == 'GET':
            a1,a2 = load_coeffs()
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            return [render(f"""
                <h2>Коефіцієнти (сума = 1)</h2>
                <form method="post">
                  a1: <input name="a1" value="{a1}" required><br>
                  a2: <input name="a2" value="{a2}" required><br>
                  <input type="submit" value="Зберегти">
                </form>
            """)]
        # POST
        try:
            a1 = float(G('a1')); a2 = float(G('a2'))
            assert abs((a1+a2)-1.0) < 1e-6
        except:
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            return [render("<p style='color:red;'>Коефіцієнти невірні.</p>")]
        save_coeffs(a1,a2)
        start_response("302 Found", [("Location","/coeffs")])
        return [b'']

    # --- Додати товар у тендер ---
    if path == '/add_item':
        products = load_products()
        if env['REQUEST_METHOD'] == 'GET':
            opts = "".join(f"<option value='{p['id']}'>{html.escape(p['name'])}</option>" for p in products)
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            return [render(f"""
                <h2>Додати товар до тендеру</h2>
                <form method="post">
                  Товар: <select name="prod">{opts}</select><br>
                  Кількість: <input name="qty" required><br>
                  <input type="submit" value="Додати">
                </form>
            """)]
        # POST
        prod = G('prod'); qty = G('qty')
        try:
            qty_f = float(qty)
            assert prod
        except:
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            return [render("<p style='color:red;'>Невірні дані.</p>")]
        items = load_tender()
        items.append({'product': prod, 'quantity': qty_f})
        save_tender(items)
        start_response("302 Found", [("Location","/add_item")])
        return [b'']

    # --- Показати тендер та вибір найкращих постачальників ---
    if path == '/tender':
        suppliers = load_suppliers()
        products  = load_products()
        prices    = load_prices()
        items     = load_tender()
        a1,a2     = load_coeffs()

        # Знаходимо Pmax та Rmax
        from collections import defaultdict
        Pmax = defaultdict(float)
        for pr in prices:
            Pmax[pr['product']] = max(Pmax[pr['product']], pr['price'])
        Rmax = max(s['rating'] for s in suppliers)

        # Формуємо таблицю
        rows = ""
        for it in items:
            pid = it['product']
            qty = it['quantity']
            # Беремо всі ціни для pid
            cand = [pr for pr in prices if pr['product']==pid]
            best = None; bestS = -1
            for pr in cand:
                sup = next(s for s in suppliers if s['id']==pr['supplier'])
                S = a1*(pr['price']/Pmax[pid]) + a2*(sup['rating']/Rmax)
                if S > bestS:
                    bestS = S
                    best = (sup, pr)
            total = best[1]['price'] * qty
            pname = next(p['name'] for p in products if p['id']==pid)
            rows += (
                f"<tr>"
                f"<td>{html.escape(pname)}</td>"
                f"<td>{qty:.2f}</td>"
                f"<td>{html.escape(best[0]['name'])}</td>"
                f"<td>{best[1]['price']:.2f}</td>"
                f"<td>{total:.2f}</td>"
                "</tr>"
            )

        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        return [render(f"""
            <h2>Результати тендеру</h2>
            <table border="1" cellpadding="4">
              <tr><th>Товар</th><th>Кількість</th><th>Постачальник</th><th>Ціна</th><th>Вартість</th></tr>
              {rows}
            </table>
        """)]

    # --- 404 ---
    start_response("404 NOT FOUND", [("Content-Type","text/plain; charset=utf-8")])
    return [b"404 Not Found"]

if __name__ == '__main__':
    print("Запускаємо WSGI-сервер на http://localhost:8051/")
    with make_server('', 8051, application) as srv:
        srv.serve_forever()
