import re


def validate_email(email):
    """
    Простая функция валидации email адреса.

    Args:
        email (str): Email адрес для проверки

    Returns:
        bool: True если email валиден, False в противном случае
    """
    if not email or not isinstance(email, str):
        return False

    # Базовый паттерн для валидации email
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    return bool(re.match(pattern, email))


if __name__ == "__main__":
    # Примеры использования
    test_emails = [
        "user@example.com",
        "test.email@domain.co.uk",
        "invalid.email",
        "@domain.com",
        "user@",
        "user@domain",
        "",
        None,
    ]

    print("Тестирование функции validate_email:")
    print("-" * 50)
    for email in test_emails:
        result = validate_email(email)
        print(f"{str(email):30} -> {result}")
