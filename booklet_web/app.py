import os
import fitz
from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def create_booklet(input_path, output_path, max_pages=8):
    doc = fitz.open(input_path)
    page_count = min(max_pages, len(doc))
    pages = [doc.load_page(i) for i in range(page_count)]

    width = doc[0].rect.width
    height = doc[0].rect.height
    blank_pdf = fitz.open()
    blank_pdf.new_page(width=width, height=height)
    blank_page_bytes = blank_pdf.convert_to_pdf()
    blank_doc = fitz.open("pdf", blank_page_bytes)

    while len(pages) % 4 != 0:
        pages.append(blank_doc[0])

    total = len(pages)
    order = []
    left = 0
    right = total - 1
    while left < right:
        order.append((pages[right], pages[left]))
        left += 1
        right -= 1
        order.append((pages[left], pages[right]))
        left += 1
        right -= 1

    output = fitz.open()
    a4_rect = fitz.paper_rect("a4")

    for p1, p2 in order:
        new_page = output.new_page(width=a4_rect.height, height=a4_rect.width)
        new_page.show_pdf_page(fitz.Rect(0, 0, a4_rect.height / 2, a4_rect.width), p1.parent, p1.number)
        new_page.show_pdf_page(fitz.Rect(a4_rect.height / 2, 0, a4_rect.height, a4_rect.width), p2.parent, p2.number)

    output.save(output_path)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['pdf']
        pages = int(request.form['pages'])
        if file:
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            output_path = os.path.join(UPLOAD_FOLDER, 'booklet_' + filename)
            file.save(input_path)
            create_booklet(input_path, output_path, max_pages=pages)
            return send_file(output_path, as_attachment=True)
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
