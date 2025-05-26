from flask import Flask, request, jsonify
from graficos import VisualizadorDatos
from datetime import datetime
from pymongo import MongoClient
import multiprocessing as mp
import requests
import time
import uuid
import logging
import os
import json



app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

logger = logging.getLogger("LOGS_INFO")
logger.setLevel(logging.INFO)

#Se carga el archivo csv
path_csv = ('./data/U_Rates.csv')


#onjeto para mandar a llamar la clase
generador_graficos = VisualizadorDatos(path_csv)

result_queue = mp.Queue()  #queue para la comunicacion entre procesos

def conexionMongo():
    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        db = client['generador_productos']
        logs_collection = db['logs']
        print("Conexion exitosa a MongoDB")
        return logs_collection
    except Exception as e:
        print(f"Error al conectar con MongoDB: {e}")
        raise


def guardar_log_en_json(message: dict):  #se cambio a dict para que reciba un diccionario

    collection = conexionMongo()
    
    logsMessage = {
        "timestamp": datetime.now().isoformat(), #usando la clase datetime 
        "operation": message.get("OPERATION", ""),
        "type": message.get("TYPE", ""),
        "read_time": message.get("READ_TIME", 0),
        "process_time": message.get("PROCESS_TIME", 0),
        "arrival_time": message.get("ARRIVAL_TIME", 0),
        "process_id": message.get("PROCESS_ID", ""),
        "status": message.get("STATUS", "")
    }

    # ruta para guardar el archivo json de los logs
    log_file = "./Logs/logs_graficos.json"
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Inicializar el archivo con una lista vacía si no existe o está corrupto
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            json.dump([], f)  # Crear archivo con un JSON válido (lista vacía)

    # Leer logs existentes
    with open(log_file, 'r') as f:
        try:
            logs = json.load(f)  # Cargar datos existentes
        except json.decoder.JSONDecodeError:
            logs = []  # Si el archivo está corrupto, empezar de nuevo

    # Agregar nuevo log y guardar
    logs.append(logsMessage)
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=4)  # Guardar con formato legible

    logger.info(logsMessage)
    collection.insert_one(logsMessage) #se inserta en mongo 
    print("LOGS INSERTADOS EN MONGO")
    
   

def generar_grafico_proceso(tipo_grafico, params, process_id, queue):
    try:
        hijo_pid = os.getpid() #se optiene el PID del proceso hijo
        log.info(f"[PROCESO HIJO] PID: {hijo_pid} - Iniciando generacion de {tipo_grafico}") #informacion cuando inicia 
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
        log.info(f"[PROCESO HIJO] PID: {hijo_pid} - {tipo_grafico} generado con exito")
        queue.put((process_id, {'Mensaje': 'Grafico generado'}))
    except Exception as e:
        #logger.error(f"[PROCESO HIJO] PID: {hijo_pid} - Error: {str(e)}")
        queue.put((process_id, {'Mensaje': 'Error', 'grafico no generado': str(e)}))

@app.route('/')
def index():
    return jsonify({"mensaje":"Servicio en ejecucion"})

@app.route("/boxplot", methods=["POST"])
def generador_boxplot():
    process_id = str(uuid.uuid4())
    data = request.get_json()
    
    arrival_time = time.time()  # Tiempo de llegada de la solicitud
    
    params = {
        "columna_x": data["columna_x"],
        "columna_y": data["columna_y"],
        "color": data["color"],
        "titulo": data["titulo"],
        "output_html": "./test/Boxplot/boxplot.html",
        "output_json": "./test/Boxplot/boxplot.json",
    }

    # Crear y iniciar proceso
    p = mp.Process(
        target=generar_grafico_proceso,
        args=("boxplot", params, process_id, result_queue),
    )
    p.start()
    # Esperar resultado con timeout
    timeStart = time.time()
    timeOut = 30  # segundos

    while True:
        try:
            if not result_queue.empty():
                current_task_id, result = result_queue.get_nowait() #se recupera un elemento de la cola
                if current_task_id == process_id:  #se verifica que el elemento coincida con su id
                    end_process_time = time.time()
                    process_time = end_process_time - timeStart
                    
                    # Log de Exito
                    message_info = {
                        "OPERATION": "CREATE_PROCESS",
                        "TYPE": "BOXPLOT",
                        "READ_TIME": end_process_time - timeStart,
                        "PROCESS_TIME": process_time,
                        "ARRIVAL_TIME": arrival_time,
                        "PROCESS_ID": process_id,
                        "STATUS": "LOG EXITO"
                    }
                    guardar_log_en_json(message_info)
                    
                    p.join()
                    return jsonify(result)

            # Verificar timeout
            if time.time() - timeStart > timeOut:
                end_process_time = time.time()
                process_time = end_process_time - timeStart
                
                # Log de timeout
                message_info = {
                    "OPERATION": "CREATE_PROCESS",
                    "TYPE": "BOXPLOT",
                    "READ_TIME": end_process_time - timeStart,
                    "PROCESS_TIME": process_time,
                    "ARRIVAL_TIME": arrival_time,
                    "PROCESS_ID": process_id,
                    "STATUS": "LOG TIMEOUT"
                }
                guardar_log_en_json(message_info)
                
                p.terminate()
                return jsonify({"Error": "Tiempo del proceso agotado"}), 504

            time.sleep(0.1)

        except Exception as e:
            end_process_time = time.time()
            process_time = end_process_time - timeStart
            
            # Log de error
            message_info = {
                "OPERATION": "CREATE_PROCESS",
                "TYPE": "BOXPLOT",
                "READ_TIME": end_process_time - timeStart,
                "PROCESS_TIME": process_time,
                "ARRIVAL_TIME": arrival_time,
                "PROCESS_ID": process_id,
                "STATUS": f"ERROR: {str(e)}"
            }
            guardar_log_en_json(message_info)
            
            p.terminate()
            return jsonify({"Error": str(e)}), 500

#EDPOINT BARRAS
@app.route('/barras', methods=['POST'])
def generador_barras():
    
    process_id = str(uuid.uuid4()) # genera ID ├║nico para cada solicitud para crear graficos
    
    data = request.get_json()
    arrival_time = time.time()  # Tiempo de llegada de la solicitud

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
    timeStart = time.time()
    timeOut = 30  # segundos

    while True:
        try:
            if not result_queue.empty():
                current_task_id, result = result_queue.get_nowait() #se recupera un elemento de la cola
                if current_task_id == process_id:  #se verifica que el elemento coincida con su id
                    end_process_time = time.time()
                    process_time = end_process_time - timeStart
                    
                    # Log de Exito
                    message_info = {
                        "OPERATION": "CREATE_PROCESS",
                        "TYPE": "BARRAS",
                        "READ_TIME": end_process_time - timeStart,
                        "PROCESS_TIME": process_time,
                        "ARRIVAL_TIME": arrival_time,
                        "PROCESS_ID": process_id,
                        "STATUS": "LOG EXITO"
                    }
                    guardar_log_en_json(message_info)
                    
                    p.join()
                    return jsonify(result)

            # Verificar timeout
            if time.time() - timeStart > timeOut:
                end_process_time = time.time()
                process_time = end_process_time - timeStart
                
                # Log de timeout
                message_info = {
                    "OPERATION": "CREATE_PROCESS",
                    "TYPE": "BARRAS",
                    "READ_TIME": end_process_time - timeStart,
                    "PROCESS_TIME": process_time,
                    "ARRIVAL_TIME": arrival_time,
                    "PROCESS_ID": process_id,
                    "STATUS": "LOG TIMEOUT"
                }
                guardar_log_en_json(message_info)
                
                p.terminate()
                return jsonify({"Error": "Tiempo del proceso agotado"}), 504

            time.sleep(0.1)

        except Exception as e:
            end_process_time = time.time()
            process_time = end_process_time - timeStart
            
            # Log de error
            message_info = {
                "OPERATION": "CREATE_PROCESS",
                "TYPE": "BARRAS",
                "READ_TIME": end_process_time - timeStart,
                "PROCESS_TIME": process_time,
                "ARRIVAL_TIME": arrival_time,
                "PROCESS_ID": process_id,
                "STATUS": f"ERROR: {str(e)}"
            }
            guardar_log_en_json(message_info)
            
            p.terminate()
            return jsonify({"Error": str(e)}), 500


#EDPOINT LINEPLOT
@app.route('/lineplot', methods=['POST'])
def generador_lineplot():
    
    process_id = str(uuid.uuid4()) # genera ID Unico para cada solicitud para crear graficos
    
    data = request.get_json()
    arrival_time = time.time()  # Tiempo de llegada de la solicitud

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
    
    timeStart = time.time()
    timeOut = 30  # segundos

    while True:
        try:
            if not result_queue.empty():
                current_task_id, result = result_queue.get_nowait() #se recupera un elemento de la cola
                if current_task_id == process_id:  #se verifica que el elemento coincida con su id
                    end_process_time = time.time()
                    process_time = end_process_time - timeStart
                    
                    # Log de Exito
                    message_info = {
                        "OPERATION": "CREATE_PROCESS",
                        "TYPE": "LINEPLOT",
                        "READ_TIME": end_process_time - timeStart,
                        "PROCESS_TIME": process_time,
                        "ARRIVAL_TIME": arrival_time,
                        "PROCESS_ID": process_id,
                        "STATUS": "LOG EXITO"
                    }
                    guardar_log_en_json(message_info)
                    
                    p.join()
                    return jsonify(result)

            # Verificar timeout
            if time.time() - timeStart > timeOut:
                end_process_time = time.time()
                process_time = end_process_time - timeStart
                
                # Log de timeout
                message_info = {
                    "OPERATION": "CREATE_PROCESS",
                    "TYPE": "LINEPLOT",
                    "READ_TIME": end_process_time - timeStart,
                    "PROCESS_TIME": process_time,
                    "ARRIVAL_TIME": arrival_time,
                    "PROCESS_ID": process_id,
                    "STATUS": "LOG TIMEOUT"
                }
                guardar_log_en_json(message_info)
                
                p.terminate()
                return jsonify({"Error": "Tiempo del proceso agotado"}), 504

            time.sleep(0.1)

        except Exception as e:
            end_process_time = time.time()
            process_time = end_process_time - timeStart
            
            # Log de error
            message_info = {
                "OPERATION": "CREATE_PROCESS",
                "TYPE": "LINEPLOT",
                "READ_TIME": end_process_time - timeStart,
                "PROCESS_TIME": process_time,
                "ARRIVAL_TIME": arrival_time,
                "PROCESS_ID": process_id,
                "STATUS": f"ERROR: {str(e)}"
            }
            guardar_log_en_json(message_info)
            
            p.terminate()
            return jsonify({"Error": str(e)}), 500

#EDPOINT SUNBURST
@app.route('/sunburst', methods=['POST'])
def generador_sunburst():
    
    process_id = str(uuid.uuid4()) # genera ID unico para cada solicitud para crear graficos
    
    data = request.get_json()
    arrival_time = time.time()  # Tiempo de llegada de la solicitud

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
    
    timeStart = time.time()
    timeOut = 30  # segundos

    while True:
        try:
            if not result_queue.empty():
                current_task_id, result = result_queue.get_nowait() #se recupera un elemento de la cola
                if current_task_id == process_id:  #se verifica que el elemento coincida con su id
                    end_process_time = time.time()
                    process_time = end_process_time - timeStart
                    
                    # Log de Exito
                    message_info = {
                        "OPERATION": "CREATE_PROCESS",
                        "TYPE": "SUNBURST",
                        "READ_TIME": end_process_time - timeStart,
                        "PROCESS_TIME": process_time,
                        "ARRIVAL_TIME": arrival_time,
                        "PROCESS_ID": process_id,
                        "STATUS": "LOG EXITO"
                    }
                    guardar_log_en_json(message_info)
                    
                    p.join()
                    return jsonify(result)

            # Verificar timeout
            if time.time() - timeStart > timeOut:
                end_process_time = time.time()
                process_time = end_process_time - timeStart
                
                # Log de timeout
                message_info = {
                    "OPERATION": "CREATE_PROCESS",
                    "TYPE": "SUNBURST",
                    "READ_TIME": end_process_time - timeStart,
                    "PROCESS_TIME": process_time,
                    "ARRIVAL_TIME": arrival_time,
                    "PROCESS_ID": process_id,
                    "STATUS": "LOG TIMEOUT"
                }
                guardar_log_en_json(message_info)
                
                p.terminate()
                return jsonify({"Error": "Tiempo del proceso agotado"}), 504

            time.sleep(0.1)

        except Exception as e:
            end_process_time = time.time()
            process_time = end_process_time - timeStart
            
            # Log de error
            message_info = {
                "OPERATION": "CREATE_PROCESS",
                "TYPE": "SUNBURST",
                "READ_TIME": end_process_time - timeStart,
                "PROCESS_TIME": process_time,
                "ARRIVAL_TIME": arrival_time,
                "PROCESS_ID": process_id,
                "STATUS": f"ERROR: {str(e)}"
            }
            guardar_log_en_json(message_info)
            
            p.terminate()
            return jsonify({"Error": str(e)}), 500

#EDPOINT MAP
@app.route('/map', methods=['POST'])
def generador_mapa():
    
    process_id = str(uuid.uuid4()) # genera ID unico para cada solicitud para crear graficos
    
    data = request.get_json()
    arrival_time = time.time()  # Tiempo de llegada de la solicitud

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
    
    timeStart = time.time()
    timeOut = 30  # segundos

    while True:
        try:
            if not result_queue.empty():
                current_task_id, result = result_queue.get_nowait() #se recupera un elemento de la cola
                if current_task_id == process_id:  #se verifica que el elemento coincida con su id
                    end_process_time = time.time()
                    process_time = end_process_time - timeStart
                    
                    # Log de Exito
                    message_info = {
                        "OPERATION": "CREATE_PROCESS",
                        "TYPE": "MAPA",
                        "READ_TIME": end_process_time - timeStart,
                        "PROCESS_TIME": process_time,
                        "ARRIVAL_TIME": arrival_time,
                        "PROCESS_ID": process_id,
                        "STATUS": "LOG EXITO"
                    }
                    guardar_log_en_json(message_info)
                    
                    p.join()
                    return jsonify(result)

            # Verificar timeout
            if time.time() - timeStart > timeOut:
                end_process_time = time.time()
                process_time = end_process_time - timeStart
                
                # Log de timeout
                message_info = {
                    "OPERATION": "CREATE_PROCESS",
                    "TYPE": "MAPA",
                    "READ_TIME": end_process_time - timeStart,
                    "PROCESS_TIME": process_time,
                    "ARRIVAL_TIME": arrival_time,
                    "PROCESS_ID": process_id,
                    "STATUS": "LOG TIMEOUT"
                }
                guardar_log_en_json(message_info)
                
                p.terminate()
                return jsonify({"Error": "Tiempo del proceso agotado"}), 504

            time.sleep(0.1)

        except Exception as e:
            end_process_time = time.time()
            process_time = end_process_time - timeStart
            
            # Log de error
            message_info = {
                "OPERATION": "CREATE_PROCESS",
                "TYPE": "MAPA",
                "READ_TIME": end_process_time - timeStart,
                "PROCESS_TIME": process_time,
                "ARRIVAL_TIME": arrival_time,
                "PROCESS_ID": process_id,
                "STATUS": f"ERROR: {str(e)}"
            }
            guardar_log_en_json(message_info)
            
            p.terminate()
            return jsonify({"Error": str(e)}), 500


if __name__ == '__main__':
    mp.freeze_support()
    app.run(host='0.0.0.0', port=5000)
