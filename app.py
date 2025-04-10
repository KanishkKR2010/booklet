import os
import fitz  # PyMuPDF
from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_booklet(input_path, output_path, from_page=1, to_page=None):
    doc = fitz.open(input_path)
    to_page = min(to_page or len(doc), len(doc))
    from_page = max(1, from_page)

    pages = [doc.load_page(i) for i in range(from_page - 1, to_page)]

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
    half_width = a4_rect.height / 2
    full_height = a4_rect.width

    for i, (p1, p2) in enumerate(order):
        new_page = output.new_page(width=a4_rect.height, height=a4_rect.width)

        # Flip every second spread
        rotate = 180 if i % 2 == 1 else 0

        # Left side
        new_page.show_pdf_page(
            fitz.Rect(0, 0, half_width, full_height),
            p1.parent,
            p1.number,
            rotate=rotate
        )

        # Right side
        new_page.show_pdf_page(
            fitz.Rect(half_width, 0, a4_rect.height, full_height),
            p2.parent,
            p2.number,
            rotate=rotate
        )

    output.save(output_path)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            file = request.files['pdf']
            from_page = int(request.form['from_page'])
            to_page = int(request.form['to_page'])

            if file:
                filename = secure_filename(file.filename)
                input_path = os.path.join(UPLOAD_FOLDER, filename)
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(UPLOAD_FOLDER, base_name + '_booklet.pdf')
                file.save(input_path)

                create_booklet(input_path, output_path, from_page=from_page, to_page=to_page)

                return send_file(output_path, as_attachment=True, download_name=f'{base_name}_booklet.pdf')

       except Exception as e:
            error_details = traceback.format_exc()
            print("❌ Failed to create booklet:", error_details)
            return f"<h2>❌ Failed to create booklet:</h2><pre>{error_details}</pre>"

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
