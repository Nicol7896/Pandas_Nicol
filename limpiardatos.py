import pandas as pa
from unidecode import unidecode


dataset = pa.read_csv('notas_estudiantes.csv')
print(dataset)


dataset["Carrera"] = dataset["Carrera"].apply(lambda x: unidecode(x.strip().title()) if isinstance (x,str)else x)
print(dataset)
dataset["Nombre"]= dataset["Nombre"].apply(lambda x: unidecode(x.strip().title())if isinstance(x,str)else x)
print(dataset)

dataset=dataset.dropna(subset=["Nombre","Edad","Carrera","Nota1","Nota2","Nota3"])
print(dataset)

dataset["Edad"]=dataset["Edad"].astype(int)
print(dataset)

dataset=dataset.drop_duplicates()
print(dataset)

dataset["Promedio"] = dataset[["Nota1","Nota2","Nota3"]].mean(axis=1)
dataset["Promedio"] = dataset["Promedio"].round(1)
print(dataset)

def clasificarpro(prome):
    if prome>= 4.5:
        return "Excelente"
    elif prome >=3.5:
        return "Bueno"
    elif prome>=2.5:
        return "Regular"
    else:
        return "Deficiente"
    
    
dataset["Desempeño"]= dataset["Promedio"].apply(clasificarpro)
print(dataset)

Nuevo=dataset.to_excel('coso.xlsx',index=False)