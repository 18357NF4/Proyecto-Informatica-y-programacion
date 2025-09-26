# -*- coding: utf-8 -*-
import socket
import json
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates

puerto=21129

temperaturas=[]
fechas=[]
tendencias=[]
colores=[]
promedios=[]
def promedio(lista):
    return sum(lista)/len(lista) if lista else 0

def actualizarGraficas(temperaturas, promedios, colores, tiempo):
    plt.clf()  
    plt.subplot(3,1,1)
    if temperaturas:
        plt.hist(temperaturas, bins=10, color="skyblue", edgecolor="black")
        plt.title("Histograma de temperaturas")
        plt.xlabel("Temperatura (°C)")
        plt.ylabel("Frecuencia")
    plt.subplot(3,1,2)
    if temperaturas and tiempo:
        plt.scatter(tiempo, temperaturas, c=colores, s=80, edgecolors="black")
        plt.title("Temperatura(t)")
        plt.xlabel("Tiempo")
        plt.ylabel("Temperatura (°C)")
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
    plt.subplot(3,1,3)
    if promedios and tiempo:
        plt.plot(tiempo,promedios, marker="o", color="blue")
        plt.title("Evolución del promedio")
        plt.xlabel("Muestras")
        plt.ylabel("Temperatura promedio (°C)")
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
    try:
        plt.tight_layout()
    except Exception as e:
        print("Aviso: tight_layout falló:", e)
    plt.pause(0.1)
    
    
servidor=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
servidor.bind(('0.0.0.0',puerto))
print('servidor vinculado al puerto')
servidor.listen(1)
conexion,direccion=servidor.accept()
print("esperando conexion")
plt.ion()
try:
    while True:
        datosRecibidos=conexion.recv(1024).decode('utf-8')
        if not datosRecibidos:
            print("el emisor cerro la conexion")
            break
        try:
            datos=json.loads(datosRecibidos)
            temp=datos['temperatura']
            fecha=datetime.strptime(datos['fecha'],"%Y-%m-%d %H:%M:%S")
            tend=datos['tendencia']
            
            temperaturas.append(temp)
            fechas.append(fecha)
            tiempo=mdates.date2num(fechas)
            tendencias.append(tend)
            promedios.append(promedio(temperaturas))
            if tend =="ALTA":
                colores.append("red")
            elif tend =="BAJA":
                colores.append("green")
            else:
                colores.append("yellow")
            actualizarGraficas(temperaturas,promedios,colores,tiempo)
        except json.JSONDecodeError:
            print("datos json invalidos")
except KeyboardInterrupt:
    print("fin de la conexion")
finally:
    conexion.close()
    servidor.close()
    plt.ioff()
