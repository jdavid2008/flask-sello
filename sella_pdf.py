import fitz  # PyMuPDF
import io
import os
import configparser
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from PIL import Image
import logging

# Configurar logging
LOG_FILE = "flask_service.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# Leer configuración desde un archivo config.ini
config = configparser.ConfigParser()
config.read("config.ini")

PATH_ENTRADA = config.get("Rutas", "PathEntrada", fallback="./entrada/")
PATH_SALIDA = config.get("Rutas", "PathSalida", fallback="./salida/")

app = Flask(__name__)


def generar_sello(texto, width=150, height=60):
    """Genera un sello en formato imagen (PNG) con fondo transparente y texto rojo."""
    packet = io.BytesIO()
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))  # Fondo transparente
    c = canvas.Canvas(packet, pagesize=(width, height))
    c.setStrokeColor(red)  # Color rojo para el borde
    c.setFillColor(red)  # Color rojo para el texto
    c.setLineWidth(2)
    c.rect(5, 5, width - 10, height - 10)  # Dibuja un rectángulo
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20, 40, texto.split("\n")[0])  # Número de registro
    c.drawString(20, 20, texto.split("\n")[1])  # Fecha y hora
    c.save()
    packet.seek(0)

    # Convertir el PDF a una imagen con transparencia usando Pillow
    sello_pdf = fitz.open("pdf", packet.read())
    pix = sello_pdf[0].get_pixmap(alpha=True)  # Habilitar canal alfa (transparencia)
    image = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)

    # Guardar la imagen en memoria en formato PNG con transparencia
    sello_img_bytes = io.BytesIO()
    image.save(sello_img_bytes, format="PNG")
    sello_img_bytes.seek(0)

    return sello_img_bytes


def agregar_sello_a_pdf(pdf_entrada, pdf_salida, codigo_registro):
    """Agrega un sello en la esquina superior derecha de la primera página de un PDF."""
    logging.info(f"Procesando PDF: {pdf_entrada} con código de registro: {codigo_registro}")
    try:
        doc = fitz.open(pdf_entrada)
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        sello_texto = f"Registro: {codigo_registro}\nFecha: {fecha_actual}"

        # Generar sello en imagen PNG con transparencia
        sello_img_bytes = generar_sello(sello_texto)

        # Guardar la imagen en el sistema de archivos temporalmente
        sello_img_path = "sello_temporal.png"
        with open(sello_img_path, "wb") as f:
            f.write(sello_img_bytes.read())

        # Obtener la primera página del documento original
        page = doc[0]
        page_width = page.mediabox.width
        page_height = page.mediabox.height

        # Definir la posición en la esquina superior derecha (ajustable)
        sello_width = 120  # Ancho del sello
        sello_height = 40  # Alto del sello
        margin = 5  # Margen desde el borde

        rect = fitz.Rect(
            page_width - sello_width - margin,  # x0 (derecha con margen)
            margin,  # y0 (arriba con margen)
            page_width - margin,  # x1 (derecha completa)
            sello_height + margin  # y1 (arriba completa)
        )

        # Insertar el sello en la primera página como imagen PNG con transparencia
        page.insert_image(rect, filename=sello_img_path)

        # Guardar el PDF con el sello agregado
        doc.save(pdf_salida)
        doc.close()

        # Eliminar imagen temporal
        os.remove(sello_img_path)

        logging.info(f"PDF sellado guardado en: {pdf_salida}")
    except Exception as e:
        logging.error(f"Error procesando PDF: {e}")


@app.route("/sellar_pdf", methods=["POST"])
def sellar_pdf():
    if "file" not in request.files or "codigo_registro" not in request.form:
        return jsonify({"error": "Se requiere un archivo PDF y un código de registro"}), 400

    archivo = request.files["file"]
    codigo_registro = request.form["codigo_registro"]

    logging.info(f" {archivo} {codigo_registro}")

    pdf_entrada = os.path.join(PATH_ENTRADA, archivo.filename)
    pdf_salida = os.path.join(PATH_SALIDA, f"sellado_{archivo.filename}")

    # Guardar el archivo de entrada
    archivo.save(pdf_entrada)
    logging.info(f"Archivo recibido: {archivo.filename}")

    # Agregar sello
    agregar_sello_a_pdf(pdf_entrada, pdf_salida, codigo_registro)

    return send_file(pdf_salida, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)