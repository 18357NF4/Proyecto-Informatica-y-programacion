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

# Definición de la placa e inicialización del iterador
board = pyfirmata.Arduino('COM7')
it = pyfirmata.util.Iterator(board)
it.start()

# Definición de objetos
sensor = Sensor(board, 1, calibracion)
boton = Boton(board, 5)
leds = Leds(board, 8, 9, 10)
time.sleep(1)  # Solo este sleep para inicialización

# Variables de estado y control
temperaturas = []
promedios = []
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

while programaActivo:
    tiempoActual = time.time()
    
    # --- CONTROL DEL BOTÓN (NO BLOQUEANTE) ---
    if boton.estaPresionado():
        if not botonPresionado:
            # Botón acaba de ser presionado
            botonPresionado = True
            midiendo = True  # Bloquear mediciones mientras se presiona el botón
            tiempoPresionInicio = tiempoActual
            tiempoUltimoDestello = tiempoActual
            print("Botón presionado, cambiando intervalo de lectura")
        
        # Destellos cada segundo mientras se mantiene presionado
        if tiempoActual - tiempoUltimoDestello >= 1.0:
            leds.destellar()
            tiempoUltimoDestello = tiempoActual
            
    else:
        if botonPresionado:
            # Botón acaba de ser liberado
            tiempoPresionado = tiempoActual - tiempoPresionInicio
            botonPresionado = False
            midiendo = False  # Permitir mediciones nuevamente
            
            print(f"Botón liberado después de {tiempoPresionado:.1f} segundos")
            
            if tiempoPresionado < 1.0:
                programaActivo = False
                print("Saliendo del programa...")
            elif 1.0 <= tiempoPresionado <= 10.0:
                intervaloLectura = tiempoPresionado
                print(f'El nuevo tiempo de lectura es de {intervaloLectura:.1f}s')
            else:
                print("Tiempo excedido, no se hace nada")
    
    # --- LECTURA DEL SENSOR (SOLO SI NO SE ESTÁ PRESIONANDO EL BOTÓN) ---
    if not botonPresionado and tiempoActual - ultimoTiempoLectura >= intervaloLectura:
        try:
            midiendo = True
            temp = sensor.leer()
            temperaturas.append(temp)
            print(f'Temperatura: {temp:.2f}°C | Promedio: {promedio(temperaturas):.2f}°C | Intervalo: {intervaloLectura:.1f}s')
            
            # Preparar para mostrar tendencia
            if len(temperaturas) >= 5:
                p = promedio(temperaturas)
                promedios.append(p)
                diferenciaActual = temperaturas[-1] - p
                mostrandoTendencia = True
                tiempoInicioTendencia = tiempoActual
            
            ultimoTiempoLectura = tiempoActual
            midiendo = False
            
        except ValueError as e:
            print(f"Error de lectura: {e}")
            midiendo = False
            ultimoTiempoLectura = tiempoActual
    
    # --- CONTROL DE LEDs (CON PRIORIDADES) ---
    # Prioridad 1: Botón presionado (destellos ya manejados arriba)
    if botonPresionado:
        # Los destellos se manejan en la sección del botón
        pass
    
    # Prioridad 2: Mostrando tendencia
    elif mostrandoTendencia:
        if tiempoActual - tiempoInicioTendencia < 0.5:
            # Seguir mostrando tendencia
            leds.marcarTendencia(diferenciaActual, error, tiempoInicioTendencia)
        else:
            # Terminó el tiempo de tendencia
            mostrandoTendencia = False
            leds.apagar()
    
    # Prioridad 3: Menos de 5 lecturas
    elif len(temperaturas) < 5 and not botonPresionado:
        leds.prender()
    
    # Prioridad 4: Estado normal (apagar LEDs)
    else:
        leds.apagar()
    
    # Pequeña pausa para no saturar la CPU
    time.sleep(0.01)

# Limpieza final
leds.apagar()
board.exit()
print("Programa terminado")
