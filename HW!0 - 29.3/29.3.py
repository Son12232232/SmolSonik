import sqlite3
import sys

DB_FILE = 'glossary.db'

def init_db():
    """Створює таблицю, якщо вона ще не існує."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS definitions (
            term TEXT PRIMARY KEY,
            description TEXT NOT NULL
        )
        """)
        conn.commit()

def add_term(term: str, description: str) -> bool:
    """
    Додає новий термін у базу.
    Повертає True, якщо успішно, False якщо термін уже є.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT INTO definitions(term, description) VALUES (?, ?)",
                (term, description)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        # PRIMARY KEY порушено — термін уже є
        return False

def get_description(term: str) -> str | None:
    """
    Шукає в базі опис для given term.
    Повертає рядок з описом, або None, якщо термін не знайдено.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute(
            "SELECT description FROM definitions WHERE term = ?",
            (term,)
        )
        row = cur.fetchone()
        return row[0] if row else None

def main():
    init_db()
    print("Глосарій термінів. Виберіть дію:")
    while True:
        print("\n1) Додати термін")
        print("2) Показати опис терміну")
        print("3) Вихід")
        choice = input("Ваш вибір: ").strip()
        if choice == '1':
            term = input("Термін: ").strip()
            desc = input("Опис   : ").strip()
            if add_term(term, desc):
                print(f"✅ Термін «{term}» додано.")
            else:
                print(f"⚠️  Термін «{term}» уже є в базі.")
        elif choice == '2':
            term = input("Введіть термін: ").strip()
            desc = get_description(term)
            if desc is None:
                print(f"❌ Термін «{term}» не знайдено.")
            else:
                print(f"ℹ️  Опис для «{term}»:\n{desc}")
        elif choice == '3':
            print("До побачення!")
            sys.exit(0)
        else:
            print("Невірний вибір, спробуйте ще.")

if __name__ == "__main__":
    main()
