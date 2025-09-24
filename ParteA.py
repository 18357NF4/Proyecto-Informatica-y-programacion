import pyfirmata
import time

calibracion = 0.1606
error = 0.3

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
    
    def marcarTendencia(self, diferencia, error, tiempo_inicio):
        """Versión no bloqueante de marcarTendencia"""
        tiempo_transcurrido = time.time() - tiempo_inicio
        self.apagar()
        
        if diferencia < -error:
            # Verde parpadeante
            if int(tiempo_transcurrido * 2) % 2 == 0:
                self.verde.write(1)
            else:
                self.verde.write(0)
        elif abs(diferencia) < error:
            # Amarillo parpadeante
            if int(tiempo_transcurrido * 2) % 2 == 0:
                self.amarillo.write(1)
            else:
                self.amarillo.write(0)
        else:
            # Rojo parpadeante
            if int(tiempo_transcurrido * 2) % 2 == 0:
                self.rojo.write(1)
            else:
                self.rojo.write(0)
        
        # La tendencia se muestra por 0.5 segundos
        return tiempo_transcurrido < 0.5

class Boton:
    def __init__(self, board, pin):
        self.board = board
        self.pin = self.board.get_pin(f'd:{pin}:i')
    
    def estaPresionado(self):
        return self.pin.read() == 1

def promedio(lista):
    n = len(lista)
    if n == 0:
        return 0
    return sum(lista) / n

# Definición de la placa e inicialización del iterador
board = pyfirmata.Arduino('COM7')
it = pyfirmata.util.Iterator(board)
it.start()

# Definición de objetos
sensor = Sensor(board, 1, 0.1637)
boton = Boton(board, 5)
leds = Leds(board, 8, 9, 10)
time.sleep(1)  # Solo este sleep para inicialización

# Variables de estado y control
temperaturas = []
intervaloLectura = 3.5
ultimoTiempoLectura = time.time()
programaActivo = True

# Variables para control no bloqueante del botón
botonPresionado = False
tiempoPresionInicio = 0
tiempoUltimoDestello = time.time()
estadoDestello = False
mostrandoTendencia = False
tiempoInicioTendencia = 0
diferenciaActual = 0

print("Sistema iniciado.")
print(f"Intervalo inicial: {intervaloLectura}s")
print("Mantén el botón presionado para cambiar el intervalo")
print("Menos de 1 segundo: Salir | 1-10 segundos: Cambiar intervalo")

# Bucle principal sin sleeps bloqueantes
while programaActivo:
    tiempoActual = time.time()
    
    # --- CONTROL DEL BOTÓN (NO BLOQUEANTE) ---
    if boton.estaPresionado():
        if not botonPresionado:
            # Botón acaba de ser presionado
            botonPresionado = True
            tiempoPresionInicio = tiempoActual
            tiempoUltimoDestello = tiempoActual
            estadoDestello = True
            leds.prender()  # Iniciar con LEDs encendidos
        
        # Destellos cada segundo mientras se mantiene presionado
        if tiempoActual - tiempoUltimoDestello >= 1.0:
            estadoDestello = not estadoDestello
            if estadoDestello:
                leds.prender()
            else:
                leds.apagar()
            tiempoUltimoDestello = tiempoActual
        
        # Verificar acciones según tiempo de presión
        tiempoPresionado = tiempoActual - tiempoPresionInicio
        
        if tiempoPresionado >= 10.0 and tiempoPresionado < 10.1:
            print("Tiempo excedido (más de 10s), manteniendo intervalo actual")
        elif tiempoPresionado >= 1.0 and tiempoPresionado <= 10.0:
            nuevoIntervalo = tiempoPresionado
            if abs(nuevoIntervalo - intervaloLectura) > 0.1:  # Evitar cambios mínimos
                intervaloLectura = nuevoIntervalo
                print(f"Nuevo intervalo de lectura: {intervaloLectura:.1f} segundos")
                
    else:
        if botonPresionado:
            # Botón acaba de ser liberado
            tiempoPresionado = tiempoActual - tiempoPresionInicio
            botonPresionado = False
            leds.apagar()
            
            if tiempoPresionado < 1.0:
                programaActivo = False
                print("Saliendo del programa...")
            else:
                print(f"Intervalo establecido: {intervaloLectura:.1f}s")
    
    # --- LECTURA DEL SENSOR SEGÚN INTERVALO ---
    if tiempoActual - ultimoTiempoLectura >= intervaloLectura:
        try:
            temp = sensor.leer()
            temperaturas.append(temp)
            print(f'Temperatura: {temp:.2f}°C | Promedio: {promedio(temperaturas):.2f}°C | Intervalo: {intervaloLectura:.1f}s')
            
            if len(temperaturas) < 5:
                # Menos de 5 lecturas: LEDs encendidos continuamente
                if not botonPresionado and not mostrandoTendencia:
                    leds.prender()
            else:
                # 5 o más lecturas: mostrar tendencia
                p = promedio(temperaturas)
                diferenciaActual = temperaturas[-1] - p
                mostrandoTendencia = True
                tiempoInicioTendencia = tiempoActual
            
            ultimoTiempoLectura = tiempoActual
            
        except ValueError as e:
            print(f"Error de lectura: {e}")
            ultimoTiempoLectura = tiempoActual
    
    # --- MOSTRAR TENDENCIA (NO BLOQUEANTE) ---
    if mostrandoTendencia:
        # Mostrar tendencia por 0.5 segundos
        if tiempoActual - tiempoInicioTendencia < 0.5:
            leds.marcarTendencia(diferenciaActual, error, tiempoInicioTendencia)
        else:
            mostrandoTendencia = False
            leds.apagar()
    
    # Pequeña pausa para no saturar la CPU (opcional, no bloqueante)
    time.sleep(0.01)

# Limpieza final
leds.apagar()
board.exit()
print("Programa terminado")
