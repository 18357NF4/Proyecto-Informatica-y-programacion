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
    if len(temperaturas):
        plt.subplot(3,1,1)
        plt.hist(temperaturas, bins=10, color="skyblue", edgecolor="black")
        plt.title("Histograma de temperaturas")
        plt.xlabel("Temperatura (°C)")
        plt.ylabel("Frecuencia")
    if len(temperaturas) > 0 and len(tiempo) > 0:
        plt.subplot(3,1,2)
        plt.scatter(tiempo, temperaturas, c=colores, s=80, edgecolors="black")
        plt.title("Temperatura(t)")
        plt.xlabel("Tiempo")
        plt.ylabel("Temperatura (°C)")
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
    if len(promedios) > 0 and len(tiempo) > 0:
        plt.subplot(3,1,3)
        plt.plot(tiempo, promedios, marker="o", color="blue")
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

# CONFIGURACIÓN MEJORADA DEL SERVIDOR
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Configurar opción para reutilizar dirección (IMPORTANTE)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    servidor.bind(('0.0.0.0', puerto))
    print(f'Servidor vinculado al puerto {puerto}')
    servidor.listen(1)
    print("Esperando conexión...")
    
    # Configurar timeout para accept (para poder cerrar con Ctrl+C)
    servidor.settimeout(1.0)
    
    plt.ion()
    plt.figure(figsize=(10, 8))
    
    conexion = None
    ejecutando = True
    
    while ejecutando:
        try:
            # Aceptar nueva conexión
            conexion, direccion = servidor.accept()
            print(f"Conexión aceptada desde: {direccion}")
            conexion.settimeout(1.0)  # Timeout para recv
            
            while True:
                try:
                    datosRecibidos = conexion.recv(1024).decode('utf-8')
                    if not datosRecibidos:
                        print("El emisor cerró la conexión")
                        break
                    
                    # Procesar múltiples mensajes en el mismo buffer
                    mensajes = datosRecibidos.strip().split('\n')
                    for mensaje in mensajes:
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
                    # Timeout normal, continuar
                    continue
                except ConnectionResetError:
                    print("Conexión resetada por el cliente")
                    break
                except BrokenPipeError:
                    print("Conexión rota")
                    break
                    
        except socket.timeout:
            # Timeout en accept, continuar para verificar KeyboardInterrupt
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
    # Cerrar conexiones de forma segura
    if conexion:
        conexion.close()
    servidor.close()
    plt.ioff()
    plt.show()
    print("Servidor cerrado correctamente")
