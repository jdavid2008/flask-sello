import requests

# Configuración
URL = "http://localhost:5000/sellar_pdf"  # Dirección del servicio Flask
PDF_ENTRADA = "Etiqueta.pdf"  # Ruta del PDF a enviar
PDF_SALIDA = "Etiqueta_sello.pdf"  # Nombre del archivo que se guardará
CODIGO_REGISTRO = "123456"  # Código de registro a incluir en el sello

# Enviar el PDF al servicio
with open(PDF_ENTRADA, "rb") as pdf_file:
    files = {"file": pdf_file}
    data = {"codigo_registro": CODIGO_REGISTRO}

    response = requests.post(URL, files=files, data=data)

# Guardar la respuesta como un archivo PDF
if response.status_code == 200:
    with open(PDF_SALIDA, "wb") as f:
        f.write(response.content)
    print(f"✅ PDF sellado guardado como {PDF_SALIDA}")
else:
    print(f"❌ Error: {response.status_code} - {response.text}")