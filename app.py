from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
import tempfile
from zipfile import ZipFile

app = Flask(__name__)

# Папки для хранения данных
CERTIFICATES_FOLDER = "static/certificates"
TEMPLATES_FOLDER = "static/templates"
FONTS_FOLDER = "static/fonts"

# Создание папок, если их нет
if not os.path.exists(CERTIFICATES_FOLDER):
    os.makedirs(CERTIFICATES_FOLDER)
if not os.path.exists(TEMPLATES_FOLDER):
    os.makedirs(TEMPLATES_FOLDER)

def validate_template_size(template_path, orientation):
    """Проверка размеров изображения."""
    expected_size = (2480, 3508) if orientation == "vertical" else (3508, 2480)
    img = Image.open(template_path)
    if img.size != expected_size:
        orientation_text = "вертикальной" if orientation == "vertical" else "горизонтальной"
        raise ValueError(
            f"Для {orientation_text} ориентации требуется размер {expected_size[0]}x{expected_size[1]} пикселей."
        )

def generate_certificate_with_image(user_name, course_title, issue_date, template_path, output_filename):
    """Генерация сертификата с использованием изображения как шаблона"""
    # Открываем шаблон
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)

    # Шрифты
    font_regular = ImageFont.truetype(f"{FONTS_FOLDER}/OpenSans-Regular.ttf", 40)
    font_bold = ImageFont.truetype(f"{FONTS_FOLDER}/OpenSans-Bold.ttf", 50)

    # Цвет текста
    text_color = (0, 0, 0)  # Черный

    # Текст
    draw.text((400, 800), "Этот сертификат подтверждает, что", font=font_regular, fill=text_color)
    draw.text((400, 1000), f"{user_name} успешно завершил курс:", font=font_regular, fill=text_color)
    draw.text((400, 1100), course_title, font=font_bold, fill=text_color)
    draw.text((400, 2000), f"Дата выдачи: {issue_date}", font=font_regular, fill=text_color)

    # Сохраняем результат
    img.save(output_filename)

@app.route("/", methods=["GET", "POST"])
def index():
    error_message = None

    if request.method == "POST":
        try:
            orientation = request.form.get("orientation", "vertical")  # Получаем ориентацию
            template_file = request.files.get("template")
            file_upload = request.files.get("file_upload")
            course_title = request.form["course_title"]
            issue_date = request.form["issue_date"]
            user_names = []

            # Сохраняем загруженный шаблон
            if template_file:
                template_path = os.path.join(TEMPLATES_FOLDER, template_file.filename)
                template_file.save(template_path)

                # Проверяем размеры изображения
                validate_template_size(template_path, orientation)
            else:
                template_path = os.path.join(TEMPLATES_FOLDER, "default_template.jpg")

            # Получаем список имен из загруженного файла или текстового поля
            if file_upload:
                file_content = file_upload.read().decode("utf-8")
                user_names = [line.strip() for line in file_content.splitlines() if line.strip()]
            else:
                user_names = request.form["user_names"].split(",")

            pdf_files = []

            # Генерация сертификатов
            for user_name in user_names:
                user_name = user_name.strip()
                output_filename = f"{CERTIFICATES_FOLDER}/{user_name}_{course_title.replace(' ', '_')}.jpg"
                generate_certificate_with_image(user_name, course_title, issue_date, template_path, output_filename)
                pdf_files.append(output_filename)

            # Если несколько сертификатов, создаем архив
            if len(pdf_files) > 1:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
                    with ZipFile(temp_zip.name, "w") as zipf:
                        for file in pdf_files:
                            zipf.write(file, os.path.basename(file))
                    temp_zip_path = temp_zip.name

                return send_file(temp_zip_path, as_attachment=True, download_name="certificates.zip")

            # Если один сертификат, возвращаем его
            return send_file(pdf_files[0], as_attachment=True)

        except ValueError as e:
            error_message = str(e)

    return render_template("index.html", error_message=error_message)

if __name__ == "__main__":
    app.run(debug=True)