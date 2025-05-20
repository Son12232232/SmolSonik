import math

def ln_ratio_series(x: float, eps: float) -> float:

    if abs(x) >= 1:
        raise ValueError("Потрібно |x|<1")

    term = x
    n = 0
    S = 0.0
    while abs(term) >= eps:
        S += term
        n += 1
        exp = 2*n + 1
        term = x**exp / exp
    return 2 * S

if __name__ == "__main__":
    eps = 1e-6
    for x in [0.1, 0.5, 0.9]:
        approx = ln_ratio_series(x, eps)
        exact  = math.log((1+x)/(1-x))
        print(f"x = {x:.1f}:")
        print(f"  Ряд:   {approx:.8f}")
        print(f"  Точно: {exact:.8f}")
        print(f"  Похибка: {abs(approx-exact):.2e}\n")
