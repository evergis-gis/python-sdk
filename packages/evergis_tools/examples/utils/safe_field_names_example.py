"""
Example: Convert field names to safe format.

This demonstrates how to use to_safe_field_name() to convert
various field names to safe database-compatible format.
"""

from evergis_tools import to_safe_field_name

print("=" * 60)
print("Safe Field Name Conversion Examples")
print("=" * 60)

# Example 1: Russian text with transliteration
print("\n1. Russian text transliteration:")
field1 = "Название Поля"
safe1 = to_safe_field_name(field1)
print(f"   '{field1}' → '{safe1}'")

field2 = "Цена за м²"
safe2 = to_safe_field_name(field2)
print(f"   '{field2}' → '{safe2}'")

# Example 2: camelCase and PascalCase
print("\n2. camelCase and PascalCase conversion:")
field3 = "fieldName"
safe3 = to_safe_field_name(field3)
print(f"   '{field3}' → '{safe3}'")

field4 = "FieldName"
safe4 = to_safe_field_name(field4)
print(f"   '{field4}' → '{safe4}'")

field5 = "HTTPResponse"
safe5 = to_safe_field_name(field5)
print(f"   '{field5}' → '{safe5}'")

# Example 3: Special characters and spaces
print("\n3. Special characters and spaces:")
field6 = "field-name with spaces"
safe6 = to_safe_field_name(field6)
print(f"   '{field6}' → '{safe6}'")

field7 = "Price ($)"
safe7 = to_safe_field_name(field7)
print(f"   '{field7}' → '{safe7}'")

field8 = "field@name#2024"
safe8 = to_safe_field_name(field8)
print(f"   '{field8}' → '{safe8}'")

# Example 4: Numbers at start
print("\n4. Numbers at the start:")
field9 = "123field"
safe9 = to_safe_field_name(field9)
print(f"   '{field9}' → '{safe9}'")

field10 = "123field"
safe10 = to_safe_field_name(field10, allow_numbers_start=True)
print(f"   '{field10}' (allow_numbers_start=True) → '{safe10}'")

# Example 5: Max length limitation
print("\n5. Maximum length limitation:")
field11 = "VeryLongFieldNameThatExceedsLimit"
safe11 = to_safe_field_name(field11, max_length=15)
print(f"   '{field11}' (max_length=15) → '{safe11}'")

field12 = "Очень Длинное Название Поля"
safe12 = to_safe_field_name(field12, max_length=20)
print(f"   '{field12}' (max_length=20) → '{safe12}'")

# Example 6: Uniqueness
print("\n6. Ensuring uniqueness:")
existing_names = {"field_name", "field_name_1"}
field13 = "fieldName"
safe13 = to_safe_field_name(field13, ensure_unique=True, existing_names=existing_names)
print(f"   '{field13}' (with existing: {existing_names}) → '{safe13}'")

# Example 7: Without snake_case conversion
print("\n7. Without snake_case conversion:")
field14 = "fieldName"
safe14 = to_safe_field_name(field14, to_snake_case=False)
print(f"   '{field14}' (to_snake_case=False) → '{safe14}'")

# Example 8: Complex mixed example
print("\n8. Complex mixed example:")
field15 = "Поле-Данных_FieldName 2024!"
safe15 = to_safe_field_name(field15, max_length=25)
print(f"   '{field15}' → '{safe15}'")

# Example 9: Batch processing
print("\n9. Batch processing multiple fields:")
fields = [
    "Имя",
    "Фамилия",
    "Дата Рождения",
    "Email Address",
    "phoneNumber",
    "ZIP-Code"
]
existing = set()
print("   Original → Safe Name")
for field in fields:
    safe = to_safe_field_name(field, ensure_unique=True, existing_names=existing)
    existing.add(safe)
    print(f"   '{field}' → '{safe}'")

print("\n" + "=" * 60)
print("✓ All examples completed successfully!")
print("=" * 60)
