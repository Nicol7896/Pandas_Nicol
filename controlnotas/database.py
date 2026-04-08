import mysql.connector
import pandas as pd
import os
import math


def conectar():
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="dashboard"
    )
    return conexion


def registrar_rechazo(nombre, edad, carrera, nota1, nota2, nota3, motivo):
    ruta_csv = os.path.join(os.path.dirname(__file__), "rechazados_estudiantes.csv")
    ruta_excel = os.path.join(os.path.dirname(__file__), "rechazados_estudiantes.xlsx")
    registro = {
        "Nombre_Estudiante": nombre,
        "Edad_Estu": edad,
        "Carrera": carrera,
        "Nota1": nota1,
        "Nota2": nota2,
        "Nota3": nota3,
        "Motivo_Rechazo": motivo,
    }

    if os.path.exists(ruta_csv):
        df_actual = pd.read_csv(ruta_csv)
        df_actual = pd.concat([df_actual, pd.DataFrame([registro])], ignore_index=True)
    else:
        df_actual = pd.DataFrame([registro])

    df_actual.to_csv(ruta_csv, index=False)
    try:
        df_actual.to_excel(ruta_excel, index=False)
    except Exception:
        pass


def contar_estudiantes():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM estudiantes")
    total = cursor.fetchone()[0]
    conexion.close()
    return total


def contar_rechazados():
    ruta_rechazados = os.path.join(os.path.dirname(__file__), "rechazados_estudiantes.csv")
    if not os.path.exists(ruta_rechazados):
        return 0
    try:
        df_rechazados = pd.read_csv(ruta_rechazados)
        return len(df_rechazados)
    except Exception:
        return 0


def cargar_estudiantes_desde_csv():
    ruta_csv = os.path.join(os.path.dirname(__file__), "..", "notas_estudiantes.csv")
    ruta_csv = os.path.abspath(ruta_csv)

    if not os.path.exists(ruta_csv):
        return

    df = pd.read_csv(ruta_csv)
    if df.empty:
        return

    df = df.rename(columns={
        "Nombre": "Nombre_Estudiante",
        "Edad": "Edad_Estu",
        "Carrera": "Carrera",
        "Nota1": "Nota1",
        "Nota2": "Nota2",
        "Nota3": "Nota3",
    })

    # Asegurarse de que las columnas existan y estén en el orden esperado
    columnas_requeridas = ["Nombre_Estudiante", "Edad_Estu", "Carrera", "Nota1", "Nota2", "Nota3"]
    if not all(col in df.columns for col in columnas_requeridas):
        return

    df = df[columnas_requeridas].copy()

    # Construir conjunto de estudiantes existentes para verificar duplicados (nombre+carrera)
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT Nombre_Estudiante, Carrera FROM estudiantes")
    existing_records = {(str(row[0]).strip().lower(), str(row[1]).strip().lower()) for row in cursor.fetchall()}

    accepted_rows = []
    rejected_rows = []
    seen_batch = set()

    for _, fila in df.iterrows():
        nombre = str(fila.get("Nombre_Estudiante", "")).strip()
        carrera = str(fila.get("Carrera", "")).strip()

        try:
            edad = float(fila.get("Edad_Estu", ""))
            if math.isnan(edad):
                edad = None
        except Exception:
            edad = None
        try:
            nota1 = float(fila.get("Nota1", ""))
            if math.isnan(nota1):
                nota1 = None
        except Exception:
            nota1 = None
        try:
            nota2 = float(fila.get("Nota2", ""))
            if math.isnan(nota2):
                nota2 = None
        except Exception:
            nota2 = None
        try:
            nota3 = float(fila.get("Nota3", ""))
            if math.isnan(nota3):
                nota3 = None
        except Exception:
            nota3 = None

        reason = []

        if not nombre or not carrera or edad is None or nota1 is None or nota2 is None or nota3 is None:
            reason.append("Datos faltantes")

        if edad is not None and edad < 0:
            reason.append("Edad negativa")

        for i, nota in enumerate([nota1, nota2, nota3], start=1):
            if nota is None or nota < 0 or nota > 5:
                reason.append(f"Nota{i} inválida")

        key = (nombre.lower(), carrera.lower())
        if key in existing_records or key in seen_batch:
            reason.append("Estudiante duplicado")

        if reason:
            rejected_rows.append({
                "Nombre_Estudiante": nombre,
                "Edad_Estu": edad,
                "Carrera": carrera,
                "Nota1": nota1,
                "Nota2": nota2,
                "Nota3": nota3,
                "Motivo_Rechazo": "; ".join(sorted(set(reason))),
            })
            continue

        accepted_rows.append((nombre, edad, carrera, nota1, nota2, nota3))
        seen_batch.add(key)

    # Insertar los aceptados
    for rec in accepted_rows:
        cursor.execute(
            "INSERT INTO estudiantes (Nombre_Estudiante, Edad_Estu, Carrera, Nota1, Nota2, Nota3) VALUES (%s,%s,%s,%s,%s,%s)",
            rec,
        )

    # Obtener total actual antes de cerrar la conexión
    cursor.execute("SELECT COUNT(*) FROM estudiantes")
    total_actual = cursor.fetchone()[0]

    conexion.commit()
    conexion.close()

    # Generar archivo CSV y Excel con rechazados (incluso si está vacío para trazar el proceso)
    ruta_rechazados_csv = os.path.join(os.path.dirname(__file__), "rechazados_estudiantes.csv")
    ruta_rechazados_xlsx = os.path.join(os.path.dirname(__file__), "rechazados_estudiantes.xlsx")
    df_rechazados_nuevo = pd.DataFrame(rejected_rows, columns=[
        "Nombre_Estudiante", "Edad_Estu", "Carrera", "Nota1", "Nota2", "Nota3", "Motivo_Rechazo"
    ])

    if os.path.exists(ruta_rechazados_csv):
        try:
            df_rechazados_existente = pd.read_csv(ruta_rechazados_csv)
            df_rechazados = pd.concat([df_rechazados_existente, df_rechazados_nuevo], ignore_index=True)
        except Exception:
            df_rechazados = df_rechazados_nuevo
    else:
        df_rechazados = df_rechazados_nuevo

    df_rechazados.to_csv(ruta_rechazados_csv, index=False)
    try:
        df_rechazados.to_excel(ruta_rechazados_xlsx, index=False)
    except Exception:
        pass

    total_rechazados = len(df_rechazados)

    duplicados = sum(
        1
        for _, r in df_rechazados.iterrows()
        if "Estudiante duplicado" in str(r.get("Motivo_Rechazo", ""))
    )

    return {
        "insertados": len(accepted_rows),
        "rechazados": total_rechazados,
        "duplicados": duplicados,
        "total_actual": total_actual,
        "archivo_rechazados": ruta_rechazados_csv,
    }


def obtener_usuarios(nombre=None):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if nombre:
        cursor.execute("SELECT * FROM usuarios WHERE nombre=%s", (nombre,))
    else:
        cursor.execute("SELECT * FROM usuarios")

    usuarios = cursor.fetchall()
    conexion.close()
    return usuarios


def obtener_estudiantes():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM estudiantes")
    estudiantes = cursor.fetchall()

    conexion.close()

    df = pd.DataFrame(estudiantes)

    if df.empty:
        cargar_estudiantes_desde_csv()

        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM estudiantes")
        estudiantes = cursor.fetchall()
        conexion.close()

        df = pd.DataFrame(estudiantes)

    if df.empty:
        # Devuelve un DataFrame vacío con las columnas esperadas para evitar KeyError en el dashboard
        df = pd.DataFrame(columns=["Nombre_Estudiante", "Edad_Estu", "Carrera", "Nota1", "Nota2", "Nota3"])

    # RENOMBRAR COLUMNAS DE MYSQL
    df = df.rename(columns={
        "Nombre_Estudiante": "nombre",
        "Edad_Estu": "edad",
        "Carrera": "carrera",
        "Nota1": "nota1",
        "Nota2": "nota2",
        "Nota3": "nota3"
    })

    # convertir a numero
    df["edad"] = pd.to_numeric(df["edad"], errors="coerce")
    df["nota1"] = pd.to_numeric(df["nota1"], errors="coerce")
    df["nota2"] = pd.to_numeric(df["nota2"], errors="coerce")
    df["nota3"] = pd.to_numeric(df["nota3"], errors="coerce")

    # calcular promedio
    df["promedio"] = (df["nota1"] + df["nota2"] + df["nota3"]) / 3

    # clasificar desempeño
    def clasificar(prom):
        if prom < 3:
            return "Bajo"
        elif prom < 4:
            return "Medio"
        else:
            return "Alto"

    df["desempenio"] = df["promedio"].apply(clasificar)

    return df


def estudiante_existe(nombre, carrera):
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT COUNT(*) AS total FROM estudiantes WHERE LOWER(TRIM(Nombre_Estudiante)) = LOWER(TRIM(%s)) AND LOWER(TRIM(Carrera)) = LOWER(TRIM(%s))",
        (nombre, carrera),
    )
    resultado = cursor.fetchone()
    conexion.close()

    return resultado and resultado[0] > 0


def insertar_estudiante(nombre, edad, carrera, nota1, nota2, nota3):
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(
        """
        INSERT INTO estudiantes
        (Nombre_Estudiante, Edad_Estu, Carrera, Nota1, Nota2, Nota3)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (nombre, edad, carrera, nota1, nota2, nota3),
    )

    conexion.commit()
    conexion.close()


if __name__ == "__main__":
    conexion = conectar()
    if conexion.is_connected():
        print("Conexión exitosa a la base de datos")
    else:
        print("Error al conectar a la base de datos")