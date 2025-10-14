import pyfirmata
import time
import csv
from datetime import datetime
import socket
import json

calibracion = 0.1606
error = 0.1

# ... (las clases Sensor, Leds, Boton se mantienen igual)
class Sensor:
    def __init__(self, board, pin, calibracion):
        self.board = board
        self.pin = self.board.get_pin(f'a:{pin}:i')
        self.calibracion = calibracion
        print("Sensor calibrado")
    
    def leer(self):
        lectura = self.pin.read()
        if lectura is None:
            raise ValueError("No se pudo leer")
        return lectura * 5 * 100 * self.calibracion

class Leds:
    def __init__(self, board, pinv, pina, pinr):
        self.board = board
        self.verde = self.board.get_pin(f'd:{pinv}:o')
        self.amarillo = self.board.get_pin(f'd:{pina}:o')
        self.rojo = self.board.get_pin(f'd:{pinr}:o')
    
    def apagar(self):
        self.verde.write(0)
        self.amarillo.write(0)
        self.rojo.write(0)
    
    def prender(self):
        self.verde.write(1)
        self.amarillo.write(1)
        self.rojo.write(1)
    
    def destellar(self):
        """Destello rápido no bloqueante"""
        self.prender()
        time.sleep(0.05)
        self.apagar()
    
    def marcarTendencia(self, diferencia, error, tiempo_inicio):
        """Versión no bloqueante de marcarTendencia"""
        tiempo_transcurrido = time.time() - tiempo_inicio
        self.apagar()
        
        if diferencia < -error:
            # Verde parpadeante
            if int(tiempo_transcurrido * 2) % 2 == 0:
                self.verde.write(1)
        elif abs(diferencia) < error:
            # Amarillo parpadeante
            if int(tiempo_transcurrido * 2) % 2 == 0:
                self.amarillo.write(1)
        else:
            # Rojo parpadeante
            if int(tiempo_transcurrido * 2) % 2 == 0:
                self.rojo.write(1)
        
        # La tendencia se muestra por 0.5 segundos
        return tiempo_transcurrido < 0.5

class Boton:
    def __init__(self, board, pin):
        self.board = board
        self.pin = self.board.get_pin(f'd:{pin}:i')
    
    def estaPresionado(self):
        return self.pin.read() == 1

def promedio(arr):
    if len(arr) == 0:
        return 0
    elif len(arr) <= 5:
        return sum(arr) / 5
    else:
        return sum(arr) / len(arr)

def valorTendencia(diferencia,promedio):
    if diferencia <-error*promedio:
        return "BAJA"
    elif abs(diferencia)<error*promedio:
        return "NINGUNA"
    else:
        return "ALTA"

def mantenerConexion(cliente, puerto, IP):
    # Verificar si la conexión actual está activa
    conexion_activa = False
    try:
        cliente.settimeout(0.5)
        cliente.recv(1, socket.MSG_PEEK)  # Verificación rápida
        conexion_activa = True
    except:
        conexion_activa = False
    
    if conexion_activa:
        return cliente  # Retorna el mismo cliente
    
    print("Conexión perdida. Iniciando reconexión...")
    cliente.close()
    
    while True:
        try:
            nuevo_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            nuevo_cliente.settimeout(3)
            resultado = nuevo_cliente.connect_ex((IP, puerto))
            
            if resultado == 0:
                print("Reconexión exitosa")
                return nuevo_cliente  # Retorna el nuevo cliente
            else:
                print(" Intento de reconexión fallido, reintentando...")
                nuevo_cliente.close()
                
        except Exception as e:
            print(f" Error en reconexión: {e}")
        
        time.sleep(3)

# --- CONFIGURACIÓN ---
#Datos para ek socket
IP_SERVIDOR="192.168.100.121"
PUERTO=21129
cliente=socket.socket(socket.AF_INET,socket.SOCK_STREAM)


# Definición de la placa e inicialización del iterador
board = pyfirmata.Arduino('COM7')
it = pyfirmata.util.Iterator(board)
it.start()

# Definición de objetos
sensor = Sensor(board, 1, calibracion)
boton = Boton(board, 5)
leds = Leds(board, 8, 9, 10)
time.sleep(1)

# Variables de estado y control
temperaturas = []
promedios = []
fechas = []
tendencias = []
intervaloLectura = 3.5
ultimoTiempoLectura = time.time()
programaActivo = True

# Flags para control de estados
botonPresionado = False
midiendo = False
mostrandoTendencia = False
tiempoInicioTendencia = 0
diferenciaActual = 0

# Variables para control del botón
tiempoPresionInicio = 0
tiempoUltimoDestello = time.time()

print("Sistema iniciado.")
print(f"Intervalo inicial: {intervaloLectura}s")
print("Mantén el botón presionado para cambiar el intervalo")
print("Menos de 1 segundo: Salir | 1-10 segundos: Cambiar intervalo")

try:
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((IP_SERVIDOR, PUERTO))
    print(f" Conectado al servidor {IP_SERVIDOR}:{PUERTO}")
    while programaActivo:
        cliente=mantenerConexion(cliente, PUERTO,IP_SERVIDOR)
        tiempoActual = time.time()  
        # --- CONTROL DEL BOTÓN ---
        if boton.estaPresionado():
            if not botonPresionado:
                botonPresionado = True
                midiendo = True
                tiempoPresionInicio = tiempoActual
                tiempoUltimoDestello = tiempoActual
                print("Botón presionado, cambiando intervalo de lectura") 
            if tiempoActual - tiempoUltimoDestello >= 1.0:
                leds.destellar()
                tiempoUltimoDestello = tiempoActual    
        else:
            if botonPresionado:
                tiempoPresionado = tiempoActual - tiempoPresionInicio
                botonPresionado = False
                midiendo = False
                print(f"Botón liberado después de {tiempoPresionado:.1f} segundos")
                if tiempoPresionado < 1.0:
                    programaActivo = False
                    print("Saliendo del programa...")
                elif 2.5 <= tiempoPresionado <= 10.0:
                    intervaloLectura = tiempoPresionado
                    print(f'El nuevo tiempo de lectura es de {intervaloLectura:.1f}s')
                else:
                    intervaloLectura = 10
        # --- LECTURA DEL SENSOR ---
        if not botonPresionado and tiempoActual - ultimoTiempoLectura >= intervaloLectura:
            midiendo = True
            temp = sensor.leer()
            temperaturas.append(temp)
            fechaHora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fechas.append(fechaHora)
            # Calcular promedio y tendencia
            p = promedio(temperaturas)
            tendencia = valorTendencia(temp - p,p)
            promedios.append(p)
            tendencias.append(tendencia)
#--BLOQUE DE TRANSMISION DE DATOS --------------------------------------------
            try:
                datos = {
                    'temperatura': temp,
                    'fecha': fechaHora,
                    'tendencia': tendencia
                }
                mensajejson = json.dumps(datos)
                cliente.send(mensajejson.encode('utf-8'))
                time.sleep(0.005)
            except (ConnectionRefusedError, ConnectionAbortedError, BrokenPipeError):
                    print("Error de conexión: el servidor cerró la conexión")
                    programaActivo = False  # salimos del loop limpio
                    break
#--BLOQUE DE MUESTREO DE TENDENCIAS Y TEMPERATURA
            print(f'Temperatura: {temp:.2f}°C | Promedio: {p:.2f}°C | Tendencia: {tendencia} | Intervalo: {intervaloLectura:.1f}s')
            # Preparar para mostrar tendencia
            if len(temperaturas) >= 5:
                diferenciaActual = temp - p
                mostrandoTendencia = True
                tiempoInicioTendencia = tiempoActual
                
            ultimoTiempoLectura = tiempoActual
            midiendo = False
            ultimoTiempoLectura = tiempoActual
        # --- CONTROL DE LEDs ---
        if botonPresionado:
            pass
        elif mostrandoTendencia:
            if tiempoActual - tiempoInicioTendencia < 0.5:
                leds.marcarTendencia(diferenciaActual, error, tiempoInicioTendencia)
            else:
                mostrandoTendencia = False
                leds.apagar()
        elif len(temperaturas) < 5 and not botonPresionado:
            leds.prender()
        else:
            leds.apagar()
        
        time.sleep(0.01)
except KeyboardInterrupt:  
    print("Programa interrumpido por el usuario")
finally:
    cliente.close()
    leds.apagar()
    board.exit()
    print("Programa terminado")
    # Guardar CSV
    with open('DatosInformatica2.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Fecha', 'Hora', 'Temperatura', 'Tendencia'])
        for i in range(len(temperaturas)):
            fecha = fechas[i]  
            temperatura = temperaturas[i] 
            tendencia = tendencias[i]
            writer.writerow([fecha, temperatura, tendencia])
