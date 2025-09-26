import pyfirmata
import time
import csv
from datetime import datetime
import socket
import json

calibracion = 0.1606
error = 0.01

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

def valorTendencia(diferencia):
    if diferencia <-error:
        return "BAJA"
    elif abs(diferencia)<error:
        return "NINGUNA"
    else:
        return "ALTA"



# --- CONFIGURACIÓN ---
#Datos para ek socket
IP_SERVIDOR="192.168.100.121"
PUERTO=1500
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
horas = []
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
    print(f"✓ Conectado al servidor {IP_SERVIDOR}:{PUERTO}")
    while programaActivo:
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
                elif 1.0 <= tiempoPresionado <= 10.0:
                    intervaloLectura = tiempoPresionado
                    print(f'El nuevo tiempo de lectura es de {intervaloLectura:.1f}s')
                else:
                    print("Tiempo excedido, no se hace nada")
        # --- LECTURA DEL SENSOR ---
        if not botonPresionado and tiempoActual - ultimoTiempoLectura >= intervaloLectura:
            midiendo = True
            temp = sensor.leer()
            temperaturas.append(temp)
            fecha = datetime.now().strftime("%Y-%m-%d")
            fechas.append(fecha)
            hora = datetime.now().strftime("%H:%M:%S")
            horas.append(hora)               
            # Calcular promedio y tendencia
            p = promedio(temperaturas)
            tendencia = valorTendencia(temp - p)
#--BLOQUE DE TRANSMISION DE DATOS --------------------------------------------
        try:
            datos = {
                'temperatura': temp,
                'fecha': fecha,
                'hora': hora,
                'tendencia': tendencia
            }
            mensajejson = json.dumps(datos)
            cliente.send(mensajejson.encode('utf-8'))
            time.sleep(0.005)
        except ConnectionRefusedError:
            # Se ejecuta si el servidor no está corriendo o la IP es incorrecta
            print(" Error: No se pudo conectar. Verifica:")
            print("  1. Que el servidor esté corriendo")
            print("  2. Que la IP y puerto sean correctos")
#--BLOQUE DE MUESTREO DE TENDENCIAS Y TEMPERATURAS
            if len(temperaturas) >= 5:
                promedios.append(p)
                tendencias.append(tendencia)
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
            hora = horas[i] 
            temperatura = temperaturas[i] 
            tendencia = tendencias[i]
            writer.writerow([fecha, hora, temperatura, tendencia])
