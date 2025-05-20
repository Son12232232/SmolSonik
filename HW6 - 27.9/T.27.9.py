from wsgiref.simple_server import make_server
from urllib.parse import parse_qs
import html

def render(body: str) -> bytes:
    html_page = (
        "<!doctype html>"
        "<html><head><meta charset='utf-8'>"
        "<title>Ск. добуток</title>"
        "</head><body>"
        f"{body}"
        "</body></html>"
    )
    return html_page.encode("utf-8")

def application(environ, start_response):
    method = environ['REQUEST_METHOD']
    if method == 'GET':
        qs = environ.get('QUERY_STRING','')
        params = parse_qs(qs, keep_blank_values=True)
    else:  # POST
        try:
            size = int(environ.get('CONTENT_LENGTH','0') or 0)
        except:
            size = 0
        data = environ['wsgi.input'].read(size).decode('utf-8')
        params = parse_qs(data, keep_blank_values=True)

    def g(key):
        vals = params.get(key)
        return vals[0] if vals else None

    n = g('n')

    if not n:
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        body = """
        <h2>Крок 1: Введіть розмір вектора n</h2>
        <form method="get">
          n: <input name="n" type="number" min="1" required><br>
          <input type="submit" value="Далі">
        </form>
        """
        return [render(body)]

    try:
        ni = int(n)
        assert ni > 0
    except:
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        return [render("<p style='color:red;'>Невірне значення n.</p>")]

    if g('v1_0') is None:
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        body = f"<h2>Крок 2: Введіть {ni} компонент(ів) вектора 1</h2>"
        body += "<form method='post'>"
        body += f"<input type='hidden' name='n' value='{n}'>"
        for i in range(ni):
            body += f"v1_{i}: <input name='v1_{i}' required><br>"
        body += "<input type='submit' value='Далі'></form>"
        return [render(body)]


    if g('v2_0') is None:
        try:
            v1 = [float(g(f'v1_{i}')) for i in range(ni)]
        except:
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
            return [render("<p style='color:red;'>Невірні дані вектора 1.</p>")]

        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        body = f"<h2>Вектор 1: [{', '.join(f'{x:.3f}' for x in v1)}]</h2>"
        body += f"<h2>Крок 3: Введіть {ni} компонент(ів) вектора 2</h2>"
        body += "<form method='post'>"
        body += f"<input type='hidden' name='n' value='{n}'>"

        for i,x in enumerate(v1):
            body += f"<input type='hidden' name='v1_{i}' value='{html.escape(str(x))}'>"
        for i in range(ni):
            body += f"v2_{i}: <input name='v2_{i}' required><br>"
        body += "<input type='submit' value='Обчислити'></form>"
        return [render(body)]

    try:
        v1 = [float(g(f'v1_{i}')) for i in range(ni)]
        v2 = [float(g(f'v2_{i}')) for i in range(ni)]
    except:
        start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
        return [render("<p style='color:red;'>Невірні дані вектора 2.</p>")]

    prod = sum(a*b for a,b in zip(v1, v2))
    body = (
        f"<h2>Вектор 1: [{', '.join(f'{x:.3f}' for x in v1)}]</h2>"
        f"<h2>Вектор 2: [{', '.join(f'{x:.3f}' for x in v2)}]</h2>"
        f"<h2>Скалярний добуток: <b>{prod:.3f}</b></h2>"
        "<p><a href='/' onclick='history.back();return false;'>Почати спочатку</a></p>"
    )
    start_response("200 OK", [("Content-Type","text/html; charset=utf-8")])
    return [render(body)]

if __name__ == '__main__':
    print("WSGI-сервер запущено на http://localhost:8051/")
    with make_server('', 8051, application) as srv:
        srv.serve_forever()
