import socket
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import time  

puerto = 21129 #puerto para la conexion socket
#arreglos para almacenar datos recibidos
temperaturas = []
fechas = []
tendencias = []
colores = []
promedios = []

def promedio(lista):
    return sum(lista) / len(lista) if lista else 0

def actualizarGraficas(temperaturas, promedios, colores, tiempo):
    plt.clf()  #limpia la figura anterior
    # Grafica 1: Histograma de temperaturas
    if len(temperaturas):
        plt.subplot(3, 1, 1)# filas, 1 columna, posicion 1
        plt.hist(temperaturas, bins=10, color="skyblue", edgecolor="black")
        plt.title("Histograma de temperaturas")
        plt.xlabel("Temperatura (°C)")
        plt.ylabel("Frecuencia")
        # Graficas 2: Dispersion de temperaturas en el tiempo
    if len(temperaturas) > 0 and len(tiempo) > 0:
        plt.subplot(3, 1, 2) # 3 filas, 1 columna, posicion 2
        plt.scatter(tiempo, temperaturas, c=colores, s=80, edgecolors="black", marker='o')
        plt.title("Temperatura(t)")
        plt.xlabel("Tiempo")
        plt.ylabel("Temperatura (°C)")
        plt.grid(True)
        # Formateo del eje X para mostrar horas:minutos:segundos
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45) # Rota las etiquetas para mejor legibilidad
      # Gráfica 3: Evolución del promedio histórico
    if len(promedios) > 0 and len(tiempo) > 0:
        plt.subplot(3, 1, 3)#3 filas, 1 columna, posición 3
        plt.plot(tiempo, promedios, marker="o", color="blue")
        plt.title("Evolución del promedio")
        plt.xlabel("Tiempo")
        plt.ylabel("Temperatura promedio (°C)")
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
        # Ajusta el layout para evitar superposiciones
    try:
        plt.tight_layout()
    except Exception as e:
        print("Aviso: tight_layout falló:", e)
    plt.pause(0.1) # Pausa breve para actualizar la visualización

def esperarConexion(servidor, puerto):
    while True:
        try:
            print("Esperando conexión del emisor...")
            conexion, direccion = servidor.accept()
            print(f"Conexión establecida con {direccion}")
            return conexion, direccion
        except Exception as e:
            print(f"Error: {e}. Reintentando en 3 segundos...")
            time.sleep(3)

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind(('0.0.0.0', puerto))
servidor.listen(1)
print('Servidor vinculado al puerto')

conexion, direccion = esperarConexion(servidor, puerto)
# --- CONFIGURACIÓN DE MATPLOTLIB ---
plt.ion() # Modo interactivo para actualizaciones en tiempo real
plt.figure(figsize=(10, 8))  # Tamaño de la ventana de gráficos

try:
    while True:
        try:
            datosRecibidos = conexion.recv(1024).decode('utf-8') # recepcion de datos escucha y recibe datos 
            
            if not datosRecibidos:
                print("Conexión cerrada. Reconectando...")
                conexion.close()
                conexion, direccion = esperarConexion(servidor, puerto)
                continue  # Vuelve al inicio del bucle
            
            # Procesar datos en formato: "temperatura|fecha|tendencia"
            partes = datosRecibidos.strip().split('|')
            
            if len(partes) == 3:
                temp = float(partes[0])# Convierte temperatura a número
                fecha_str = partes[1]  # Fecha como string
                tend = partes[2] # Tendencia como string
                
                # Convertir string de fecha a objeto datetime
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                
                temperaturas.append(temp)
                fechas.append(fecha)
                tiempo = mdates.date2num(fechas) # Convierte fechas a formato numérico de matplotlib
                tendencias.append(tend)
                promedios.append(promedio(temperaturas))
                
                # Asignar colores según la tendencia
                if tend == "ALTA":
                    colores.append("red")
                elif tend == "BAJA":
                    colores.append("green")
                else:
                    colores.append("gold")
                    
                actualizarGraficas(temperaturas, promedios, colores, tiempo)
                
                # Mostrar datos en consola
                print(f"Recibido: {temp:.2f}°C | {fecha_str} | {tend}")
                
            else:
                print(f"Datos en formato incorrecto: {datosRecibidos}")
                
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
            print(f"Conexión perdida ({e}). Reconectando...")
            conexion.close()
            conexion, direccion = esperarConexion(servidor, puerto)
        except ValueError as e:
            print(f"Error procesando datos: {e} - Datos: {datosRecibidos}")
            
except KeyboardInterrupt:
    print("Fin de la conexión por usuario")
finally:
    conexion.close()
    servidor.close()
    plt.ioff() # Desactiva el modo interactivo de matplotlib
    print("Programa terminado")
