import pandas as pd
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors


def cargar_datos(ruta):
    df= pd.read_csv(ruta)
    return df

def explorar(df):
    print("Primeras filas")
    print(df.head())
    print("\n Informacion del DataFrame")
    df.info()
    print("\n Estadistica descriptiva")
    print(df.describe())

def salariopxgenero(df):
    Promedio = df.groupby("gender")["salary"].mean()
    return Promedio

def generomasalario(prom):
    return prom.idxmax(),prom.max()

def promedios(df):
    edades = df["age"].mean()
    Promedios = df["salary"].mean()
    Media =df["salary"].median()
    Dis = df ["salary"].std()
    
    return edades,Promedios,Media,Dis

def rangosdeedad(df):
    bins=[18,30,40,50,60,100]
    labels = ["18-30","31-40","41-50","51-60","60+"]
    df["rango_edad"]=pd.cut(df["age"],bins=bins,labels=labels)
    df.groupby("rango_edad")["salary"].mean()
    Promedioed = df .groupby("rango_edad")["salary"].mean()
    return Promedioed

def probabilidadsalario(df,valor):
    
    probalid=(df["salary"]>valor).mean()*100
    return probalid

def clas_salario(df):
    bins = [0, 5000, 8000, float('inf')]  
    labels = ["Bajo", "Medio", "Alto"] 
    df["clasificacion_salario"] = pd.cut(df["salary"], bins=bins, labels=labels, right=False)
    return df



def generar_pdf(dataf,nompdf):
    docu=SimpleDocTemplate(nompdf)
    styles= getSampleStyleSheet()
    elemen = []
    
    Spersonalizado= ParagraphStyle('miestilo',
                                   parent = styles['Normal'],
                                   fontName='Helvetica',
                                   textColor=colors.blue,
                                   spaceAfter=10)
    
    data= [dataf.columns.tolist()] + dataf.values.tolist()
    tabla = Table(data)
    
    elemen.append(Paragraph("REPORTE DE ANALISIS DE SALARIO",Spersonalizado))
    elemen.append(tabla)
    docu.build(elemen)
    print(f'PDF{nompdf}Documento Generado')
    
    
    
    


def main():    
    df=cargar_datos('data.csv')
    print(df)   
    explorar(df)
    Prome = salariopxgenero(df)
    edades,Promedios,Media,Dis= promedios(df)
    print("Salario promedio por genero")
    print(Prome.round(0).astype(int))
    genero,salario = generomasalario(Prome)
    print(f"Genero con mayor salario {genero} (${salario:.2f})")
    print(f"Edad promedio: {edades}")
    print("Salario Promedio",round(Promedios,2))
    print("Media del salario",round(Media,2))
    print("Desviacion del salario",round(Dis,2))
    dt=rangosdeedad(df)
    print(dt)
    print(f'Salario promedio por rango de edad:{dt.round(2)}')
    print(f'Probabilidad salario > 8000={probabilidadsalario(df,8000):.2f}')
    
    df = clas_salario(df)
    print("\nClasificación de salarios:")
    print(df[["salary", "clasificacion_salario"]])
    
    df.to_csv("Analisis.csv",index=False)
    print("archivo csv generado")
    
    
    analisis = pd.DataFrame({
        "Indicador":[
            "Salario Promedio Female",
            "Salario Promedio Masculino",
            "Genero con mayor Salario",
            "Edad Promedio",
            "Salario Promedio",
            "Media Salario",
            "Desviacion del salario",
            "Salario promedio por rango de edad",
            "Probabilidad Salario >8000",
            "Clasificacion de Salario"
            ],
        "Valor":[
    Prome.get("Female",0),
    Prome.get("Male",0),
    genero,
    round(edades,2),
    round(Promedios,2),
    round(Media,2),
    round(Dis,2),
    dt.round(2).to_dict(),
    round(probabilidadsalario(df,8000),2),
    "Ver Analisis.csv"
]

    })
 
    analisis.to_csv("analisis_salarios.csv", index=False)
    print("Reporte creado")
    generar_pdf(analisis,"Analisis de  salarios.pdf")
   
    
    
main()

