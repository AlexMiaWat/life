import datetime
import os
from pathlib import Path

# Директории: исходная и целевая
docs_dir = Path("docs")  # Корень docs
output_dir = Path("plans")  # Директория для master
output_file = output_dir / "master_docs_index.md"

# Создаём plans, если нет
output_dir.mkdir(exist_ok=True)

# Собираем все .md файлы рекурсивно
md_files = []
for root, dirs, files in os.walk(docs_dir):
    for file in files:
        if file.endswith(".md"):
            full_path = Path(root) / file
            relative_path = full_path.relative_to(
                docs_dir
            )  # Относительный путь от docs/
            md_files.append((relative_path, full_path))

# Сортируем по пути для логичной структуры
md_files.sort(key=lambda x: x[0])

# Генерируем содержимое master
with open(output_file, "w", encoding="utf-8") as master:
    # Заголовок
    master.write("# Master Docs Index: Объединённая документация проекта Life\n\n")
    master.write(
        "Этот файл — индекс всех .md из docs/. Создан автоматически для удобного поиска и навигации.\n"
    )
    master.write(
        f'**Дата генерации:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n'
    )

    # Оглавление (TOC) с якорями
    master.write("## Оглавление\n")
    for rel_path, _ in md_files:
        anchor = (
            str(rel_path).replace("/", "-").replace("\\", "-").replace(".md", "")
        )  # Якорь: путь-как-строка
        master.write(f"- [{rel_path}](#{anchor})\n")
    master.write("\n")

    # Содержимое каждого файла
    for rel_path, full_path in md_files:
        anchor = str(rel_path).replace("/", "-").replace("\\", "-").replace(".md", "")
        master.write(
            f'## {rel_path} <a id="{anchor}"></a>\n'
        )  # Заголовок с путём и якорем
        master.write(f"**Полный путь:** docs/{rel_path}\n\n")
        master.write("```markdown\n")
        with open(full_path, "r", encoding="utf-8") as md:
            master.write(md.read())
        master.write("```\n\n")
        master.write("---\n\n")

    master.write("# Конец индекса\n")

print(
    f"Готово: {output_file} сгенерирован. Размер: {os.path.getsize(output_file)} байт."
)
