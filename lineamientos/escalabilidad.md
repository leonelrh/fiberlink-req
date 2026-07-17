## Lineamientos de Escalabilidad

Objetivos:
- Busca que la aplicación soporte la demanda actual y futura.
- Responde a: ¿La aplicación soportará el volumen esperado sin degradarse?

Lineamientos:
- ESC-01: La solución debe diseñarse con base en una volumetría estimada y revisable.
- ESC-02: Deben definirse objetivos de latencia para procesos críticos.
- ESC-03: Los componentes deben poder escalar horizontalmente cuando sea posible.
- ESC-04: Debe utilizarse caché en lecturas frecuentes cuando agregue valor y no comprometa la consistencia requerida.
- ESC-05: Las operaciones pesadas, diferibles o de integración no crítica deben ejecutarse de forma asíncrona.
- ESC-06: Deben prevenirse cuellos de botella en base de datos, red, broker de eventos o sistemas on premises.
- ESC-07: Deben establecerse límites de concurrencia, cuotas y estrategias de backpressure.
- ESC-08: Deben ejecutarse pruebas de carga para validar la arquitectura.

