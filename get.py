import os
from pathlib import Path


def collect_python_code(output_file="python_code.txt", project_root=None):
    """
    Собирает все Python файлы проекта в один текстовый файл
    """
    # Если не указана корневая папка, используем текущую
    if project_root is None:
        project_root = os.getcwd()

    project_root = Path(project_root)
    output_path = project_root / output_file

    print(f"📁 Поиск Python файлов в: {project_root}")

    # Папки, которые нужно игнорировать
    exclude_dirs = {'.git', '.venv', 'venv', '__pycache__', 'migrations'}

    with open(output_path, 'w', encoding='utf-8') as f_out:
        files_count = 0

        # Рекурсивно обходим все папки
        for root, dirs, files in os.walk(project_root):
            # Убираем исключенные папки из списка для обхода
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                # Проверяем, что это Python файл
                if file.endswith('.py'):
                    file_path = Path(root) / file

                    try:
                        # Получаем относительный путь от корня проекта
                        relative_path = file_path.relative_to(project_root)

                        # Читаем содержимое файла
                        with open(file_path, 'r', encoding='utf-8') as f_in:
                            content = f_in.read()

                        # Записываем путь к файлу
                        f_out.write(f"{relative_path}\n")
                        f_out.write("=" * 60 + "\n")

                        # Записываем содержимое
                        f_out.write(content)

                        # Разделитель между файлами
                        f_out.write("\n\n" + "#" * 60 + "\n\n")

                        files_count += 1
                        print(f"✓ {relative_path}")

                    except UnicodeDecodeError:
                        print(f"✗ {relative_path} (ошибка чтения)")
                    except Exception as e:
                        print(f"✗ {file_path}: {e}")

    print(f"\n✅ Готово! Найдено {files_count} Python файлов")
    print(f"📄 Результат сохранен в: {output_path}")
    return output_path


# Самый простой способ использования - просто запустить скрипт
if __name__ == "__main__":
    collect_python_code()