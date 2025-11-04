import pyfirmata
import time
import csv
from datetime import datetime
import socket


calibracion = 0.1606 #factor de calibracion para el sensor 
error = 0.01 #margen para determinar tendencia 

class Sensor:
    def __init__(self, board, pin, calibracion):
        #con esto la clase directamente configura el pin digital de entrada
        self.board = board
        self.pin = self.board.get_pin(f'a:{pin}:i')
        self.calibracion = calibracion
        print("Sensor calibrado")
    
    def leer(self):
        #lee el valor y hace la conversion de temperatura
        lectura = self.pin.read()
        if lectura is None:
            raise ValueError("No se pudo leer")
        return lectura * 5 * 100 * self.calibracion

class Leds:
    def __init__(self, board, pinv, pina, pinr):
        #configura los 3 leds en las salidas de pines digitales
        self.board = board
        self.verde = self.board.get_pin(f'd:{pinv}:o')
        self.amarillo = self.board.get_pin(f'd:{pina}:o')
        self.rojo = self.board.get_pin(f'd:{pinr}:o')
    
    def apagar(self):
        #apaga los leds
        self.verde.write(0)
        self.amarillo.write(0)
        self.rojo.write(0)
    
    def prender(self):
        #prende los leds
        self.verde.write(1)
        self.amarillo.write(1)
        self.rojo.write(1)
    
    def destellar(self):
        #destello de los leds
        self.prender()
        time.sleep(0.05)
        self.apagar()
    
    def marcarTendencia(self, diferencia, error,promedio):
        #controla los leds segun la tendencia calculada
        self.apagar()
        if diferencia < -error*promedio:
                self.verde.write(1)
        elif abs(diferencia) < error*promedio:
                self.amarillo.write(1)
        else:
                self.rojo.write(1)
        
class Boton:
    def __init__(self, board, pin):
        #configura el boton al pin digital de entrada
        self.board = board
        self.pin = self.board.get_pin(f'd:{pin}:i')
    
    def estaPresionado(self):
        #verifiaca si el boton esta presionado
        return self.pin.read() == 1

def promedio(arr):
    if len(arr) == 0:
        return 0
    elif len(arr) <= 5:
        return sum(arr) / 5
    else:
        return sum(arr) / len(arr)

def valorTendencia(diferencia,promedio):
    #determina la tendencia en fucion de la diferencia con el promedio
    if diferencia <-error*promedio:
        return "BAJA"
    elif abs(diferencia)<error*promedio:
        return "NINGUNA"
    else:
        return "ALTA"

def mantenerConexion(cliente, puerto, IP):
    #verifica y mantiene la conexion con el servidor
    try:
        cliente.setblocking(False)
        try:
            data = cliente.recv(1024, socket.MSG_PEEK)
            if data == b'':
                raise ConnectionError("Servidor desconectado")
        except BlockingIOError:
            pass
        except ConnectionResetError:
            raise ConnectionError("Conexión reseteada")
        finally:
            cliente.setblocking(True)
        return cliente
    except (ConnectionError, OSError, socket.error,ConnectionAbortedError,socket.timeout) as e:
        print(f"Conexión perdida ({e}). Iniciando reconexión...")
        try:
            cliente.close()
        except:
            pass
        while True:
            try:
                nuevo_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                nuevo_cliente.settimeout(3)
                resultado = nuevo_cliente.connect_ex((IP, puerto))
                if resultado == 0:
                    print("Reconexión exitosa")
                    return nuevo_cliente
                else:
                    print("Intento de reconexión fallido, reintentando...")
                    nuevo_cliente.close()
            except Exception as e:
                print(f"Error en reconexión: {e}")
            time.sleep(3)

# --- CONFIGURACIÓN ---
#Datos para el socket
IP_SERVIDOR="192.168.213.111"
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
temperaturas = [] #historial de temperaturas
promedios = [] #promedios calculados 
fechas = [] #fecha y horas de la lecturas
tendencias = [] #tendencias en cada lecturas
intervaloLectura = 2.5
ultimoTiempoLectura = time.time()
programaActivo = True

# Flags para control de estados
botonPresionado = False #si el boton esta siendo presionado
midiendo = False #si se esta realizando una medicion
mostrandoTendencia = False # si se esta mostrando tendencia con LEDs
tiempoInicioTendencia = 0 #Cuando empezo a mostrarse la tendencia 
diferenciaActual = 0 #diferencia actual con el promedio

# Variables para control del botón
tiempoPresionInicio = 0 #cuando se empezo a presionar el boton
tiempoUltimoDestello = time.time() #ultimo destellos de LED

print("Sistema iniciado.")
print(f"Intervalo inicial: {intervaloLectura}s")
print("Mantén el botón presionado para cambiar el intervalo")
print("Menos de 1 segundo: Salir | 1-10 segundos: Cambiar intervalo")

try:
    #conexion inicial al servidor
    cliente.connect((IP_SERVIDOR, PUERTO))
    print(f" Conectado al servidor {IP_SERVIDOR}:{PUERTO}")
    while programaActivo:
        #mantiene la conexion con el servidor 
        cliente=mantenerConexion(cliente, PUERTO,IP_SERVIDOR)
        tiempoActual = time.time()  
        # --- CONTROL DEL BOTÓN ---
        if boton.estaPresionado():
            if not botonPresionado:
                #inicio de presion del boton
                botonPresionado = True
                midiendo = True
                tiempoPresionInicio = tiempoActual
                tiempoUltimoDestello = tiempoActual
                print("Botón presionado, cambiando intervalo de lectura") 
                #destellos de LEDs cada segundno mientras se presiona
            if tiempoActual - tiempoUltimoDestello >= 1.0:
                leds.destellar()
                tiempoUltimoDestello = tiempoActual    
        else:
            if botonPresionado:
                #boton liberado-> procesar el tiempo de presion
                tiempoPresionado = tiempoActual - tiempoPresionInicio
                botonPresionado = False
                midiendo = False
                print(f"Botón liberado después de {tiempoPresionado:.1f} segundos")
                # acciones segun el tiempo de presion
                if tiempoPresionado < 1.0:
                    programaActivo = False #salir del programa
                    print("Saliendo del programa...")
                elif 2.5 <= tiempoPresionado <= 10.0: #cambiar el intervalo
                    intervaloLectura = tiempoPresionado
                    print(f'El nuevo tiempo de lectura es de {intervaloLectura:.1f}s')
                else:
                    intervaloLectura = 10 #intervalos maximo por defecto
        # --- LECTURA DEL SENSOR ---
        if not botonPresionado and tiempoActual - ultimoTiempoLectura >= intervaloLectura:
            midiendo = True
            #lectura y procesamiento de datos
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
                mensaje = f"{temp:.2f}|{fechaHora}|{tendencia}"
                cliente.send(mensaje.encode('utf-8'))
            except (ConnectionRefusedError, ConnectionAbortedError, BrokenPipeError):
                print("Error de conexión")
#--BLOQUE DE MUESTREO DE TENDENCIAS Y TEMPERATURA
            print(f'Temperatura: {temp:.2f}°C | Promedio: {p:.2f}°C | Tendencia: {tendencia} | Intervalo: {intervaloLectura:.1f}s')
            if len(temperaturas) >= 5:
                diferenciaActual = temp - p
                mostrandoTendencia = True
                tiempoInicioTendencia = tiempoActual    
            ultimoTiempoLectura = tiempoActual
            midiendo = False
        # --- CONTROL DE LEDs ---
        if botonPresionado:
            pass #mostrar tendencia con LEDs parpadeantes por 0.5 segundos
        elif mostrandoTendencia:
            if tiempoActual - tiempoInicioTendencia < 0.05:
                leds.prender()
            else:
                mostrandoTendencia = False
                leds.apagar()
        elif not mostrandoTendencia:
            if tiempoActual - tiempoInicioTendencia > 0.4 and tiempoActual - tiempoInicioTendencia <2:
                leds.marcarTendencia(diferenciaActual,error,p)
        elif len(temperaturas) < 5 and not botonPresionado:
            #Leds encendisos hasta tener 5 lecturas
            leds.prender()
        else:
            #apaga los LEds en estado normal
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
