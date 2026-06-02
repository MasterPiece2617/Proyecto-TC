Este proyecto implementa la interconexión formal y concurrente de dos autómatas finitos (el Cajero Automático y el Banco Central) utilizando hilos independientes (`threading`) y comunicación por paso de mensajes (`queue`). La renderización visual de los estados dinámicos y el Stack de mensajes IPC se genera en tiempo real en un lienzo estático unificado mediante **Graphviz**.

---

## 1. Requisitos e Instalación de Graphviz

Para que el script pueda de manera dinámica dibujar el grafo animado `system_live.png`, es obligatorio tener instalado el motor de renderizado **Graphviz** en el sistema operativo y el paquete de enlace para Python.

## 2. Instalar la librería de Python
En cualquier sistema operativo, ejecuta el siguiente comando en tu terminal para instalar la interfaz de control:

```bash
pip install graphviz
```
## 3. Instalar el Binario del Sistema Operativo 

En Windows (vía Winget) Abre la terminal de Windows (PowerShell o CMD) como Administrador y ejecuta el siguiente comando para instalar Graphviz de forma automatizada:
```bash
winget install Graphviz.Graphviz
```

En Linux en la mayoría de las distribuciones, el motor dot se encuentra directamente en los repositorios oficiales. Ábrelo en tu terminal y escribe:
```bash
sudo apt install graphviz
```

## 4. Ejecutar desde la Terminal:

```bash
python main.py
```

## 5. Visualizar grafos:

Abrir `system_live.png` en el editor de texto para ver los cambios en tiempo real.