# Proyecto: Sistema de Actualización de Archivo Maestro
# Framework: Flask
# Estructura general del backend (app.py) con módulos para cargar, actualizar y descargar archivos

from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta'

# Ruta de almacenamiento temporal y del archivo maestro
UPLOAD_FOLDER = 'uploads'
MASTER_FILE = os.path.join(UPLOAD_FOLDER, 'archivo_maestro.xlsx')
LOG_FILE = os.path.join(UPLOAD_FOLDER, 'log_actualizaciones.txt')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ------------------------ MÓDULO 1: INICIO / DASHBOARD ------------------------
@app.route('/')
def dashboard():
    if os.path.exists(MASTER_FILE):
        fecha_actualizacion = datetime.fromtimestamp(os.path.getmtime(MASTER_FILE)).strftime('%d/%m/%Y %H:%M')
        tamaño = os.path.getsize(MASTER_FILE)
    else:
        fecha_actualizacion = 'No disponible'
        tamaño = 0
    return render_template('dashboard.html', fecha=fecha_actualizacion, tamaño=tamaño)

# ------------------------ MÓDULO 2: CARGAR DATOS CAMBIABLES ------------------------
@app.route('/cargar', methods=['GET', 'POST'])
def cargar():
    if request.method == 'POST':
        archivo = request.files['archivo']
        if archivo:
            ruta = os.path.join(UPLOAD_FOLDER, 'datos_nuevos.xlsx')
            archivo.save(ruta)
            try:
                df = pd.read_excel(ruta)
                preview = df.head(10).to_html()
                return render_template('cargar.html', preview=preview, cargado=True)
            except Exception as e:
                flash(f"Error al procesar el archivo: {e}")
    return render_template('cargar.html', cargado=False)

# ------------------------ MÓDULO 3: ACTUALIZAR ARCHIVO MAESTRO ------------------------
@app.route('/actualizar', methods=['POST'])
def actualizar():
    try:
        nuevos = pd.read_excel(os.path.join(UPLOAD_FOLDER, 'datos_nuevos.xlsx'))
        if os.path.exists(MASTER_FILE):
            maestro = pd.read_excel(MASTER_FILE)
            actualizados = pd.concat([maestro, nuevos]).drop_duplicates().reset_index(drop=True)
        else:
            actualizados = nuevos
        actualizados.to_excel(MASTER_FILE, index=False)

        with open(LOG_FILE, 'a') as f:
            f.write(f"Actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Filas: {len(nuevos)}\n")

        flash("Archivo maestro actualizado correctamente.")
    except Exception as e:
        flash(f"Error durante la actualización: {e}")
    return redirect(url_for('dashboard'))

# ------------------------ MÓDULO 4: DESCARGAR ARCHIVO ACTUALIZADO ------------------------
@app.route('/descargar/<formato>')
def descargar(formato):
    if not os.path.exists(MASTER_FILE):
        flash("No hay archivo maestro para descargar.")
        return redirect(url_for('dashboard'))
    df = pd.read_excel(MASTER_FILE)
    ruta_descarga = os.path.join(UPLOAD_FOLDER, f'maestro_actualizado.{formato}')
    if formato == 'csv':
        df.to_csv(ruta_descarga, index=False)
    elif formato == 'xlsx':
        df.to_excel(ruta_descarga, index=False)
    else:
        flash("Formato no soportado aún.")
        return redirect(url_for('dashboard'))
    return send_file(ruta_descarga, as_attachment=True)

# ------------------------ MÓDULO 5: HISTORIAL DE CAMBIOS ------------------------
@app.route('/historial')
def historial():
    historial = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            historial = f.readlines()
    return render_template('historial.html', historial=historial)

# ------------------------ MÓDULO 6 y 7: Configuración y Ayuda ------------------------
@app.route('/configuracion')
def configuracion():
    return render_template('configuracion.html')

@app.route('/ayuda')
def ayuda():
    return render_template('ayuda.html')

# ------------------------ INICIO ------------------------
if __name__ == '__main__':
    app.run(debug=True)
