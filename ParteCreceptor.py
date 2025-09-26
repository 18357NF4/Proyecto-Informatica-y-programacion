import socket
import json
import matplotlib.pyplot as plt
from datetime import datetime

puerto=21129

temperaturas=[]
fechas=[]
tendencias=[]
colores=[]
promedios=[]
def promedio(lista):
    return sum(lista)/len(lista) if lista else 0

def actualizarGraficas(temperaturas,promedios,colores,tiempo):
    plt.subplot(3,1,1)
    plt.cla()
    plt.hist(temperaturas)
    plt.title("Histograma de temperaturas")
    plt.xlabel("temperaturas")
    plt.ylabel("frecuencia simple")
    
    plt.subplot(3,1,2)
    plt.cla()
    plt.scatter(tiempo,temperaturas,c=colores,s=80,edgecolors="black")
    plt.title("Temperatura(t)")
    plt.xlabel("temperatura")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.ylabel("Tiempo")
    
    plt.subplot(3,1,3)
    plt.cla()
    plt.plot(promedios)
    plt.title("evolucion del promedio")
    plt.xlabel("temperatura")
    plt.ylabel("frecuencia simple")
    
    plt.tight_layout()
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
            fecha=datetime.strptime(datos['fecha'],"$Y-%m-%d %H:%M:%S")
            tend=datos['tendencia']
            
            temperaturas.append(temp)
            fechas.append(fecha)
            tendencias.append(tend)
            promedios.append(promedio(temperaturas))
            if tend =="ALTA":
                colores.append("red")
            elif tend =="BAJA":
                colores.append("green")
            else:
                colores.append("yellow")
            actualizarGraficas(temperaturas,promedios,colores)
        except json.JSONDecodeError:
            print("datos json invalidos")
except KeyboardInterrupt:
    print("fin de la conexion")
finally:
    conexion.close()
    servidor.close()

