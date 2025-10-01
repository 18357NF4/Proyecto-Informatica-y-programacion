# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import socket
import json
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates

puerto = 21129

temperaturas = []
fechas = []
tendencias = []
colores = []
promedios = []

def promedio(lista):
    return sum(lista)/len(lista) if lista else 0

def actualizarGraficas(temperaturas, promedios, colores, tiempo):
    plt.clf()  
    
    # Histograma de temperaturas
    plt.subplot(3,1,1)
    if temperaturas: # La condición es más concisa
        plt.hist(temperaturas, bins=10, color="skyblue", edgecolor="black")
    plt.title("Histograma de Temperaturas")
    plt.xlabel("Temperatura (°C)")
    plt.ylabel("Frecuencia")
    
    # Gráfico de dispersión de temperatura vs. tiempo
    plt.subplot(3,1,2)
    if temperaturas and tiempo: # La condición es más concisa
        plt.scatter(tiempo, temperaturas, c=colores, s=80, edgecolors="black")
    plt.title("Temperatura vs. Tiempo") # Título más descriptivo
    plt.xlabel("Tiempo")
    plt.ylabel("Temperatura (°C)")
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    
    # Gráfico de evolución del promedio
    plt.subplot(3,1,3)
    if promedios and tiempo: # La condición es más concisa
        plt.plot(tiempo, promedios, marker="o", color="blue")
    plt.title("Evolución del Promedio Acumulado") # Título más preciso
    plt.xlabel("Tiempo")
    plt.ylabel("Temperatura promedio (°C)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    
    try:
        plt.tight_layout()
    except Exception as e:
        print("Aviso: tight_layout falló:", e)
    plt.pause(0.1)

# CONFIGURACIÓN MEJORADA DEL SERVIDOR
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    servidor.bind(('0.0.0.0', puerto))
    print(f'Servidor vinculado al puerto {puerto}')
    servidor.listen(1)
    print("Esperando conexión...")
    servidor.settimeout(1.0)
    
    plt.ion()
    plt.figure(figsize=(10, 8))
    
    conexion = None
    ejecutando = True
    
    while ejecutando:
        try:
            conexion, direccion = servidor.accept()
            print(f"Conexión aceptada desde: {direccion}")
            conexion.settimeout(1.0)
            
            # Búfer de recepción para mensajes incompletos
            buffer_recepcion = ""

            while True:
                try:
                    # Se lee un fragmento de datos
                    datosRecibidos = conexion.recv(1024).decode('utf-8')
                    if not datosRecibidos:
                        print("El emisor cerró la conexión")
                        break
                    
                    # Se añaden los datos al búfer
                    buffer_recepcion += datosRecibidos
                    
                    # Procesar mensajes completos (delimitados por '\n')
                    while '\n' in buffer_recepcion:
                        mensaje, buffer_recepcion = buffer_recepcion.split('\n', 1)
                        if mensaje:
                            try:
                                datos = json.loads(mensaje)
                                temp = datos['temperatura']
                                fecha = datetime.strptime(datos['fecha'], "%Y-%m-%d %H:%M:%S")
                                tend = datos['tendencia']
                                
                                temperaturas.append(temp)
                                fechas.append(fecha)
                                tiempo = mdates.date2num(fechas)
                                tendencias.append(tend)
                                promedios.append(promedio(temperaturas))
                                
                                if tend == "ALTA":
                                    colores.append("red")
                                elif tend == "BAJA":
                                    colores.append("green")
                                else:
                                    colores.append("yellow")
                                
                                actualizarGraficas(temperaturas, promedios, colores, tiempo)
                                print(f"Datos recibidos: {temp}°C, {tend}")
                                
                            except json.JSONDecodeError:
                                print("Datos JSON inválidos:", mensaje)
                            except KeyError as e:
                                print(f"Clave faltante en JSON: {e}")
                            except ValueError as e:
                                print(f"Error en formato de fecha: {e}")
                
                except socket.timeout:
                    continue
                except (ConnectionResetError, BrokenPipeError):
                    print("Conexión perdida con el cliente.")
                    break
        
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            print("\nFin de la conexión por interrupción del usuario")
            ejecutando = False
        except Exception as e:
            print(f"Error inesperado: {e}")
            ejecutando = False

except OSError as e:
    print(f"Error al iniciar servidor: {e}")
    print("Posiblemente el puerto está en uso. Cierra otros programas que usen el puerto 21129")

finally:
    if conexion:
        conexion.close()
    servidor.close()
    plt.ioff()
    plt.show()
    print("Servidor cerrado correctamente")
