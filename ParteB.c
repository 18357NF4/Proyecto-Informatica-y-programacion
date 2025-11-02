#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>
// Definición de la estructura para almacenar cada lectura del sensor
typedef struct {
    char fecha[20]; // Almacena la fecha en formato string
    char hora[10]; // Almacena la hora en formato string 
    double temperatura; // Almacena el valor de temperatura como número decimal
    char tendencias;  // Almacena la tendencia como un solo carácter
} lecturas;

lecturas* leer_csv(const char *nombre_del_archivo, int *total) {
   // Intenta abrir el archivo en modo lectura
    FILE *archivo = fopen(nombre_del_archivo, "r");
    if (!archivo) {
        printf("Error al abrir el archivo");
        return NULL; 
    }

    char linea[256]; // Buffer para almacenar cada línea del archivo
    int capacidad = 10; // Capacidad inicial del arreglo dinámico
    int contador = 0;  // Contador de lecturas procesadas
    lecturas *lectura = malloc(capacidad * sizeof(lecturas)); // Reserva memoria inicial
     // Lee y descarta la primera línea (encabezados)
    fgets(linea, sizeof(linea), archivo);
    // Procesa cada línea del archivo
    while (fgets(linea, sizeof(linea), archivo) != NULL) {
         // Si se llena la capacidad, aumenta el tamaño del arreglo
        if (contador >= capacidad) {
            capacidad += 10;
            lectura = realloc(lectura, capacidad * sizeof(lecturas));
        }
   // Divide la línea usando comas como separadores
        char *token = strtok(linea, ",");
        if (token) {
            // Copia la fecha (primer token)
            strcpy(lectura[contador].fecha, token);
            // Obtiene el segundo token (temperatura)
            token = strtok(NULL, ",");
            if (token) {
                // Convierte el string a número decimal
                lectura[contador].temperatura = atof(token);
                // Obtiene el tercer token (tendencia)
                token = strtok(NULL, ",\r\n");
                if (token) {
                    // Toma solo el primer carácter de la tendencia
                    lectura[contador].tendencias = token[0];
                }
            }
            contador++; // Incrementa el contador de lecturas
        }
    }

    fclose(archivo); // Cierra el archivo
    *total = contador;  // Retorna el total de lecturas
    printf("Se leyeron %d lecturas correctamente\n", contador); 
    return lectura; // Retorna el arreglo con los datos
}

void find(lecturas lectura[], int total) {
    if (total <= 0) {
        printf("No hay datos para analizar.\n");
        return;
    }
    // Inicializa con los valores de la primera lectura
    double mayor = lectura[0].temperatura;
    double menor = lectura[0].temperatura;
    int posmayor = 0; // Índice de la temperatura máxima
    int posmenor = 0; // Índice de la temperatura mínima
// Recorre todas las lecturas buscando máximos y mínimos
    for(int i = 1; i < total; i++) {
        if (lectura[i].temperatura > mayor) {
            mayor = lectura[i].temperatura;
            posmayor = i;
        }
        if (lectura[i].temperatura < menor) {
            menor = lectura[i].temperatura;
            posmenor = i;
        }
    }
    // Muestra los resultados
    printf("La mayor temperatura registrada fue de: %.2f°C y se tomo el dia %s a las %s\n",
           mayor, lectura[posmayor].fecha, lectura[posmayor].hora);
    printf("La menor temperatura registrada fue de: %.2f°C y se tomo el dia %s a las %s\n",
           menor, lectura[posmenor].fecha, lectura[posmenor].hora);
}

void prom_desvestandar(lecturas lectura[], int total) {
    if (total <= 0) {
        printf("No hay datos para calcular.\n");
        return;
    }
    double promedio = 0, desvestandar = 0;
    // promedio
    double sum1 = 0;
    for (int i = 0; i < total; i++) {
        sum1 += lectura[i].temperatura; 
    }
    promedio = sum1 / total;
    //desviacion estandar
    double sum2 = 0;
    for (int i = 0; i < total; i++) {
        sum2 += (lectura[i].temperatura - promedio) * (lectura[i].temperatura - promedio);
    }
    desvestandar = sqrt(sum2 / total);

    printf("La media es de %.2f\n", promedio);
    printf("La desviacion estandar es de %.2f\n", desvestandar);
}
/**
 * Función de comparación para qsort - ordena números de menor a mayor
 */
int comparar_doubles(const void *a, const void *b) {
    double diff = (*(double*)a - *(double*)b);
    if (diff > 0) return 1;
    if (diff < 0) return -1;
    return 0;
}

void calcular_mediana_temperaturas(lecturas datos[], int total) {
    if (total <= 0) {
        printf("No hay datos para calcular mediana.\n");
        return; 
    }
    // Crea un arreglo temporal solo con las temperaturas
    double *temperaturas = malloc(total * sizeof(double));
    for(int i = 0; i < total; i++) {
        temperaturas[i] = datos[i].temperatura;
    }
    // Ordena las temperaturas de menor a mayor
    qsort(temperaturas, total, sizeof(double), comparar_doubles);  

    double mediana;
    if (total % 2 == 1) {
        // Calcula la mediana según si el total es par o impar
        mediana = temperaturas[total / 2];
    } else {
        // Si es par: promedio de los dos valores centrale
        mediana = (temperaturas[total / 2 - 1] + temperaturas[total / 2]) / 2.0;
    }

    free(temperaturas);
    printf("La mediana es %.2f\n", mediana);  
}
void moda(lecturas datos[], int total) {
    if (total <= 0) {
        printf("No hay datos para calcular moda.\n");
        return;
    }
    
    int max_frecuencia = 0;     // Frecuencia máxima encontrada
    double moda_valor = datos[0].temperatura;  // Valor de la moda
    int frec_actual = 0;        // Frecuencia temporal
    
    // Compara cada temperatura con todas las demás
    for(int i = 0; i < total; i++) {
        frec_actual = 0;  // Reinicia contador para cada temperatura
        
        // Cuenta cuántas veces aparece esta temperatura
        for(int j = 0; j < total; j++) {
            if(datos[i].temperatura == datos[j].temperatura) {
                frec_actual++;  // Incrementa si encuentra temperatura igual
            }
        }
        
        // Actualiza la moda si encuentra una frecuencia mayor
        if (frec_actual > max_frecuencia) {
            max_frecuencia = frec_actual;
            moda_valor = datos[i].temperatura;
        }
    }
    
    printf("La moda es: %.2f (aparece %d veces)\n", moda_valor, max_frecuencia);
}
int main() {
    int total; // Variable para almacenar el número total de lecturas
    const char *nombre_fijo = "C:/Users/giuli/facu/2do/segundo semestre/informatica y progrmacion/proyecto_final/DatosInformatica2.csv";
     // Lee los datos del archivo CSV
    lecturas *lectura = leer_csv(nombre_fijo, &total);
    // Verifica si se pudieron leer los datos correctamente
    if (lectura == NULL || total == 0) {
        printf("No se pudieron leer datos del archivo '%s'.\n", nombre_fijo);
        printf("Verifica que la ruta sea correcta y el archivo exista.\n");
        return 1;
    }

    printf("Datos cargados correctamente desde: %s\n", nombre_fijo);
    printf("Se procesaron %d lecturas.\n", total);

    find(lectura, total);
    prom_desvestandar(lectura, total);
    calcular_mediana_temperaturas(lectura, total);
    moda(lectura,total);
    free(lectura);
    return 0;
}
