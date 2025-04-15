from flask import Flask, request, jsonify
from graficos import VisualizadorDatos
import multiprocessing as mp
import requests
import time
import uuid
import logging
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Se carga el archivo csv
path_csv = ('./data/U_Rates.csv')


#onjeto para mandar a llamar la clase
generador_graficos = VisualizadorDatos(path_csv)

result_queue = mp.Queue()  #queue para la comunicación entre procesos

def generar_grafico_proceso(tipo_grafico, params, process_id, queue):
    try:
        hijo_pid = os.getpid() #se optiene el PID del proceso hijo
        logger.info(f"[PROCESO HIJO] PID: {hijo_pid} - Iniciando generación de {tipo_grafico}") #informacion cuando inicia 
        if tipo_grafico == 'boxplot':
            generador_graficos.generar_grafico_boxplot(**params) #genera el grafico boxplot
        elif tipo_grafico == 'barras':
            generador_graficos.generar_grafico_barras(**params)  #genera el grafico barras
        elif tipo_grafico == 'lineplot':
            generador_graficos.generar_grafico_line(**params)
        elif tipo_grafico == 'sunburst':
            generador_graficos.generar_grafico_sunburst(**params)
        elif tipo_grafico == 'map':
            generador_graficos.generar_mapa(**params)
        logger.info(f"[PROCESO HIJO] PID: {hijo_pid} - {tipo_grafico} generado con éxito")
        queue.put((process_id, {'Mensaje': 'Grafico generado'}))
    except Exception as e:
        logger.error(f"[PROCESO HIJO] PID: {hijo_pid} - Error: {str(e)}")
        queue.put((process_id, {'Mensaje': 'Error', 'grafico no generado': str(e)}))

@app.route('/')
def index():
    return jsonify({"mensaje":"Servicio en ejecucion"})

@app.route('/boxplot', methods=['POST'])
def generador_boxplot():
    
    process_id = str(uuid.uuid4()) # genera ID único para cada solicitud para crear graficos
    
    data = request.get_json()

    params = {
        'columna_x': data['columna_x'],
        'columna_y': data['columna_y'],
        'color': data['color'],
        'titulo': data['titulo'],
        'output_html': './test/Boxplot/boxplot.html',
        'output_json': './test/Boxplot/boxplot.json'
    }
    
    # Crear y iniciar clase Process para iniciar el proceso
    p = mp.Process(
        target=generar_grafico_proceso,
        args=('boxplot', params, process_id, result_queue)
    )
    p.start()
    
    # Esperar resultado con timeout
    timeStart = time.time()
    timeOut = 30  # segundos
    
    while True:
        try:
            # Revisar la cola sin bloquear
             #empty() devuelve True si la cola está vacía.
            if not result_queue.empty(): 
                current_task_id, result = result_queue.get_nowait()  #se recupera un elemento de la cola
                if current_task_id == process_id: #se verifica que el elemento coincida con su id
                    p.join()  # Esperar a que termine el proceso
                    return jsonify(result)
            
            # Verificar timeout
            if time.time() - timeStart > timeOut: #Verifica si se pasa del tiempo de 30s
                p.terminate() #termina el proceso 
                return jsonify({'Error': 'Tiempo del proceso agotado'}), 504
                
            time.sleep(0.1)  # Pequeña pausa para evitar CPU al 100%
            
        except Exception as e:
            p.terminate()
            return jsonify({'Error': str(e)}), 500

#EDPOINT BARRAS
@app.route('/barras', methods=['POST'])
def generador_barras():
    
    process_id = str(uuid.uuid4()) # genera ID único para cada solicitud para crear graficos
    
    data = request.get_json()

    params = {
        'columna_x': data['columna_x'],
        'columna_y': data['columna_y'],
        'color': data['color'],
        'titulo': data['titulo'],
        'output_html': './test/Barras/barras.html',
        'output_json': './test/Barras/barras.json'
    }
    
    # Crear y iniciar clase Process para iniciar el proceso
    p = mp.Process(
        target=generar_grafico_proceso,
        args=('barras', params, process_id, result_queue)
    )
    p.start()
    
    # Esperar resultado con timeout
    timeStart = time.time()
    timeOut = 30  # segundos
    
    while True:
        try:
            # Revisar la cola sin bloquear
             #empty() devuelve True si la cola está vacía.
            if not result_queue.empty(): 
                current_task_id, result = result_queue.get_nowait()  #se recupera un elemento de la cola
                if current_task_id == process_id: #se verifica que el elemento coincida con su id
                    p.join()  # Esperar a que termine el proceso
                    return jsonify(result)
            
            # Verificar timeout
            if time.time() - timeStart > timeOut: #Verifica si se pasa del tiempo de 30s
                p.terminate() #termina el proceso 
                return jsonify({'Error': 'Tiempo del proceso agotado'}), 504
                
            time.sleep(0.1)  # Pequeña pausa para evitar CPU al 100%
            
        except Exception as e:
            p.terminate()
            return jsonify({'Error': str(e)}), 500


#EDPOINT LINEPLOT
@app.route('/lineplot', methods=['POST'])
def generador_lineplot():
    
    process_id = str(uuid.uuid4()) # genera ID único para cada solicitud para crear graficos
    
    data = request.get_json()

    params = {
        'columna_x': data['columna_x'],
        'columna_y': data['columna_y'],
        'color': data['color'],
        'titulo': data['titulo'],
        'output_html': './test/Lineplot/lineplot.html',
        'output_json': './test/Lineplot/lineplot.json'
    }
    
    # Crear y iniciar clase Process para iniciar el proceso
    p = mp.Process(
        target=generar_grafico_proceso,
        args=('lineplot', params, process_id, result_queue)
    )
    p.start()
    
    # Esperar resultado con timeout
    timeStart = time.time()
    timeOut = 30  # segundos
    
    while True:
        try:
            # Revisar la cola sin bloquear
             #empty() devuelve True si la cola está vacía.
            if not result_queue.empty(): 
                current_task_id, result = result_queue.get_nowait()  #se recupera un elemento de la cola
                if current_task_id == process_id: #se verifica que el elemento coincida con su id
                    p.join()  # Esperar a que termine el proceso
                    return jsonify(result)
            
            # Verificar timeout
            if time.time() - timeStart > timeOut: #Verifica si se pasa del tiempo de 30s
                p.terminate() #termina el proceso 
                return jsonify({'Error': 'Tiempo del proceso agotado'}), 504
                
            time.sleep(0.1)  # Pequeña pausa para evitar CPU al 100%
            
        except Exception as e:
            p.terminate()
            return jsonify({'Error': str(e)}), 500

#EDPOINT SUNBURST
@app.route('/sunburst', methods=['POST'])
def generador_sunburst():
    
    process_id = str(uuid.uuid4()) # genera ID único para cada solicitud para crear graficos
    
    data = request.get_json()

    params = {
        'jerarquia': data['jerarquia'],
        'valores': data['valores'],
        'titulo': data['titulo'],
        'output_html': './test/Sunburst/sunburst.html',
        'output_json': './test/Sunburst/sunburst.json'
    }
    
    # Crear y iniciar clase Process para iniciar el proceso
    p = mp.Process(
        target=generar_grafico_proceso,
        args=('sunburst', params, process_id, result_queue)
    )
    p.start()
    
    # Esperar resultado con timeout
    timeStart = time.time()
    timeOut = 30  # segundos
    
    while True:
        try:
            # Revisar la cola sin bloquear
             #empty() devuelve True si la cola está vacía.
            if not result_queue.empty(): 
                current_task_id, result = result_queue.get_nowait()  #se recupera un elemento de la cola
                if current_task_id == process_id: #se verifica que el elemento coincida con su id
                    p.join()  # Esperar a que termine el proceso
                    return jsonify(result)
            
            # Verificar timeout
            if time.time() - timeStart > timeOut: #Verifica si se pasa del tiempo de 30s
                p.terminate() #termina el proceso 
                return jsonify({'Error': 'Tiempo del proceso agotado'}), 504
                
            time.sleep(0.1)  # Pequeña pausa para evitar CPU al 100%
            
        except Exception as e:
            p.terminate()
            return jsonify({'Error': str(e)}), 500

#EDPOINT MAP
@app.route('/map', methods=['POST'])
def generador_mapa():
    
    process_id = str(uuid.uuid4()) # genera ID único para cada solicitud para crear graficos
    
    data = request.get_json()

    params = {
        'geojson_url': 'https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json',
        'locations': data['locations'],
        'featureidkey': 'properties.name',
        'color': data['color'],
        'color_continuous_scale': 'burg',
        'titulo': data['titulo'],
        'output_html': './test/Map/mapa.html',
        'output_json': './test/Map/mapa.json'
    }
    
    # Crear y iniciar clase Process para iniciar el proceso
    p = mp.Process(
        target=generar_grafico_proceso,
        args=('map', params, process_id, result_queue)
    )
    p.start()
    
    # Esperar resultado con timeout
    timeStart = time.time()
    timeOut = 30  # segundos
    
    while True:
        try:
            # Revisar la cola sin bloquear
             #empty() devuelve True si la cola está vacía.
            if not result_queue.empty(): 
                current_task_id, result = result_queue.get_nowait()  #se recupera un elemento de la cola
                if current_task_id == process_id: #se verifica que el elemento coincida con su id
                    p.join()  # Esperar a que termine el proceso
                    return jsonify(result)
            
            # Verificar timeout
            if time.time() - timeStart > timeOut: #Verifica si se pasa del tiempo de 30s
                p.terminate() #termina el proceso 
                return jsonify({'Error': 'Tiempo del proceso agotado'}), 504
                
            time.sleep(0.1)  # Pequeña pausa para evitar CPU al 100%
            
        except Exception as e:
            p.terminate()
            return jsonify({'Error': str(e)}), 500

"""""
@app.route('/boxplot', methods=['POST'])
def generador_boxplot():
    #Se obtienen los datos json
    data = request.get_json()
    
    output_html=('./test/Boxplot/boxplot.html')
    output_json=('./test/Boxplot/boxplot.json')
    
    generador_graficos.generar_grafico_boxplot(
        columna_x= data.get('columna_x'), 
        columna_y= data.get('columna_y'),    
        color = data.get('color'),
        titulo=data.get('titulo'),
        output_html=output_html,
        output_json=output_json
    )
    return jsonify({"Mensaje": "Grafico boxplot generado"})

@app.route('/barras', methods=['POST'])
def generador_barras():
    data = request.get_json()

    output_html=('./test/Barras/barras.html')
    output_json=('./test/Barras/barras.json')

    generador_graficos.generar_grafico_barras(
        columna_x= data.get('columna_x'),
        columna_y= data.get('columna_y'),    
        color = data.get('color'),
        titulo= data.get('titulo'),
        output_html=output_html,
        output_json=output_json
    )
    return jsonify({"Mensaje": "Grafico de barras generado"})

@app.route('/lineplot', methods=['POST'])
def generador_lineplot():
    data = request.get_json()

    output_html=('./test/Lineplot/lineplot.html')
    output_json=('./test/Lineplot/lineplot.json')

    generador_graficos.generar_grafico_line(
        columna_x= data.get('columna_x'),
        columna_y= data.get('columna_y'),    
        color = data.get('color'),
        titulo= data.get('titulo'),
        output_html=output_html,
        output_json=output_json
    )
    return jsonify({"Mensaje": "Grafico de lineplot generado"})

@app.route('/sunburst', methods=['POST'])
def generador_sunburst():
    data = request.get_json()
    output_html=('./test/Sunburst/sunburst.html')
    output_json=('./test/Sunburst/sunburst.json')

    generador_graficos.generar_grafico_sunburst(
        jerarquia= data.get('jerarquia'),  #Este valor si es unico va dentro de [''] en el json
        valores= data.get('valores'),     
        titulo= data.get('titulo'),
        output_html=output_html,
        output_json=output_json
    )
    return jsonify({"Mensaje": "Grafico de sunburst generado"})
"""

if __name__ == '__main__':
    mp.freeze_support()
    app.run(host='0.0.0.0', port=5000)

