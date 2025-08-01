import re

# Тестируем разные форматы аргументов
test_cases = [
    "path='test_quotes.txt', content='Test quotes'",
    'path="test_quotes.txt", content="Test quotes"',
    "'test_quotes.txt', 'Test quotes'",
    '"test_quotes.txt", "Test quotes"'
]

for args_str in test_cases:
    print(f"Args: {args_str}")
    quoted_args = re.findall(r'["\']([^"\']*)["\']', args_str)
    print(f"Quoted args: {quoted_args}")
    print() 