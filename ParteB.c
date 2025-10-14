#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>

typedef struct {
    char fecha[20];
    char hora[10];
    double temperatura;
    char tendencias;
} lecturas;

lecturas* leer_csv(const char *nombre_del_archivo, int *total) {
    FILE *archivo = fopen(nombre_del_archivo, "r");
    if (!archivo) {
        printf("Error al abrir el archivo");
        return NULL;
    }

    char linea[256];
    int capacidad = 10;
    int contador = 0;
    lecturas *lectura = malloc(capacidad * sizeof(lecturas));

    fgets(linea, sizeof(linea), archivo);

    while (fgets(linea, sizeof(linea), archivo) != NULL) {
        if (contador >= capacidad) {
            capacidad *= 2;
            lectura = realloc(lectura, capacidad * sizeof(lecturas));
        }

        char *token = strtok(linea, ",");
        if (token) {
            strcpy(lectura[contador].fecha, token);

            token = strtok(NULL, ",");
            if (token) {
                lectura[contador].temperatura = atof(token);

                token = strtok(NULL, ",\r\n");
                if (token) {
                    lectura[contador].tendencias = token[0];
                }
            }
            contador++;
        }
    }

    fclose(archivo);
    *total = contador;
    printf("Se leyeron %d lecturas correctamente\n", contador);
    return lectura;
}

void find(lecturas lectura[], int total) {
    if (total <= 0) {
        printf("No hay datos para analizar.\n");
        return;
    }
    double mayor = lectura[0].temperatura;
    double menor = lectura[0].temperatura;
    int posmayor = 0;
    int posmenor = 0;

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

    double *temperaturas = malloc(total * sizeof(double));
    for(int i = 0; i < total; i++) {
        temperaturas[i] = datos[i].temperatura;
    }

    qsort(temperaturas, total, sizeof(double), comparar_doubles);  // CORRECCIÓN: función correcta

    double mediana;
    if (total % 2 == 1) {
        mediana = temperaturas[total / 2];
    } else {
        mediana = (temperaturas[total / 2 - 1] + temperaturas[total / 2]) / 2.0;
    }

    free(temperaturas);
    printf("La mediana es %.2f\n", mediana);  // CORRECCIÓN: faltaba ; y \n
}

int main() {
    int total;
    const char *nombre_fijo = "C:/Users/ignac/Documents/Python/DatosInformatica2.csv";

    lecturas *lectura = leer_csv(nombre_fijo, &total);

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

    free(lectura);
    return 0;
}
