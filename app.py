
from flask import Flask, redirect, render_template, request, session, send_file
import pandas
import os

from dashboard import creartablero
from database import conectar, insertar_estudiante, cargar_estudiantes_desde_csv, estudiante_existe, registrar_rechazo, contar_estudiantes, contar_rechazados
from pandas import isna

pd=pandas

server = Flask(__name__)
server.secret_key = "190305"


@server.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


#Funcion para quitar acentos/tildes

def quitar_acentos(texto):
    if pd.isna(texto):
        return texto 
    
    
        texto=str(texto)
        return ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )


@server.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["nombre"]
        password = request.form["password"]

        conn = conectar()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM usuarios WHERE Username=%s AND Password_User=%s",
            (username, password),
        )

        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            session["nombre"] = usuario["Username"]
            session["rol"] = usuario["Rol_Usu"]
            return redirect("/tablero/")

        return render_template(
            "login.html",
            error="Usuario o contrasena incorrectos",
        )

    return render_template("login.html")


@server.route("/insertar_estudiante/", methods=["POST", "GET"])
def insertar_estudiante_route():
    if "nombre" not in session:
        return redirect("/")

    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        edad_raw = request.form["edad"]
        carrera = request.form["carrera"].strip()
        nota1_raw = request.form["nota1"]
        nota2_raw = request.form["nota2"]
        nota3_raw = request.form["nota3"]

        # Validaciones básicas
        errores = []

        try:
            edad = int(edad_raw)
            if edad < 0:
                errores.append("Edad negativa")
        except Exception:
            edad = None
            errores.append("Edad inválida")

        try:
            nota1 = float(nota1_raw)
            nota2 = float(nota2_raw)
            nota3 = float(nota3_raw)
        except Exception:
            nota1 = nota2 = nota3 = None
            errores.append("Notas inválidas")

        if nota1 is not None and (nota1 < 0 or nota1 > 5):
            errores.append("Nota1 fuera de rango")
        if nota2 is not None and (nota2 < 0 or nota2 > 5):
            errores.append("Nota2 fuera de rango")
        if nota3 is not None and (nota3 < 0 or nota3 > 5):
            errores.append("Nota3 fuera de rango")

        if not nombre:
            errores.append("Nombre vacío")
        if not carrera:
            errores.append("Carrera vacía")

        if estudiante_existe(nombre, carrera):
            errores.append("Estudiante duplicado")

        if errores:
            motivo = "; ".join(errores)
            registrar_rechazo(nombre, edad, carrera, nota1, nota2, nota3, motivo)
            return render_template(
                "registro_estudiante.html",
                error=f"Registro rechazado: {motivo}",
            )

        insertar_estudiante(nombre, edad, carrera, nota1, nota2, nota3)
        return redirect("/tablero/")

    return render_template("registro_estudiante.html")


@server.route("/carga_masiva/")
def carga_masiva_route():
    if "nombre" not in session:
        return redirect("/")

    resultado = cargar_estudiantes_desde_csv() or {
        "insertados": 0,
        "rechazados": 0,
        "duplicados": 0,
        "archivo_rechazados": "rechazados_estudiantes.csv",
    }

    total_rechazados = contar_rechazados()

    return render_template(
        "carga_masiva.html",
        insertados=resultado.get("insertados", 0),
        rechazados=total_rechazados,
        duplicados=resultado.get("duplicados", 0),
        archivo_rechazados=resultado.get("archivo_rechazados", "rechazados_estudiantes.csv"),
    )


@server.route("/descargar_rechazados")
def descargar_rechazados_route():
    if "nombre" not in session:
        return redirect("/")

    ruta_csv = os.path.join(os.path.dirname(__file__), "rechazados_estudiantes.csv")
    ruta_xlsx = os.path.join(os.path.dirname(__file__), "rechazados_estudiantes.xlsx")

    if os.path.exists(ruta_csv):
        return send_file(
            ruta_csv,
            mimetype="text/csv",
            as_attachment=True,
            download_name="rechazados_estudiantes.csv",
        )
    elif os.path.exists(ruta_xlsx):
        return send_file(
            ruta_xlsx,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="rechazados_estudiantes.xlsx",
        )

    return "No se encontró el archivo de rechazados. Ejecute primero la carga masiva.", 404


@server.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@server.before_request
def proteger_tablero():
    if request.path.startswith("/tablero") and "nombre" not in session:
        return redirect("/")
    return None

def calculardesempeño(nota1, nota2, nota3):
    promedio = (nota1 + nota2 + nota3) / 3
    if promedio >= 4.5:
        return "Excelente"
    elif promedio >= 3.5:
        return "Bueno"
    elif promedio >= 2.5:
        return "Regular"
    else:
        return "Deficiente"


creartablero(server)


if __name__ == "__main__":
    server.run(debug=True)
