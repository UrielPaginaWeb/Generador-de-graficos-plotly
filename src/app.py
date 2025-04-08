from flask import Flask, request, jsonify
from graficos import VisualizadorDatos

app = Flask(__name__)

#Se carga el archivo csv
path_csv = ('./data/U_Rates.csv')

#onjeto para mandar a llamar la clase
generador_graficos = VisualizadorDatos(path_csv)

@app.route('/')
def index():
    return jsonify({"mensaje":"Index"})
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)