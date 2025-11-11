# app.py
# Importa las librerías necesarias
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sympy import sympify, diff, sqrt, integrate, symbols, lambdify, latex
import numpy as np
import os # Necesario para que send_from_directory funcione correctamente

# Inicializar la aplicación Flask
# 'static_folder=None' previene conflictos con la ruta raíz
app = Flask(__name__, static_folder=None)

# Configurar CORS (Aunque ahora servimos todo desde el mismo origen, 
# es bueno mantenerlo por si acaso)
CORS(app)

# --- RUTA PARA SERVIR LA PÁGINA WEB (index.html) ---
# Esta es la nueva ruta que hace que tu app esté autocontenida
@app.route('/')
def index():
    # Sirve el archivo 'index.html' desde el directorio actual ('.')
    return send_from_directory('.', 'index.html')

# --- RUTA PARA LA API DE CÁLCULO ---
@app.route('/calcular', methods=['POST'])
def calcular_longitud_arco():
    # 1. Obtener los datos JSON enviados desde el frontend
    datos = request.json
    funcion_str = datos['funcion']
    a_str = datos['limite_a']
    b_str = datos['limite_b']
    
    pasos = [] # Lista para almacenar los pasos de la solución
    try:
        # 2. Convertir límites a números de punto flotante
        a = float(a_str)
        b = float(b_str)

        # 3. Detectar la variable automáticamente (x, y, z, etc.)
        f = sympify(funcion_str) # Convertir el string a una expresión SymPy
        
        variables = f.free_symbols # Obtener las variables (ej: {x})
        
        if len(variables) > 1:
            # Error si la función tiene más de una variable (ej: "x*y")
            raise Exception(f"La función debe tener solo una variable, pero se encontraron: {variables}")
        elif len(variables) == 0:
            variable = symbols('x') # Usar 'x' por defecto si es una constante (ej: "5")
        else:
            variable = variables.pop() # Obtener la variable encontrada (ej: 'y' o 'z')

        # 4. Generar el LaTeX para la función principal (para la vista previa)
        funcion_latex = f"f({variable}) = {latex(f)}"
        pasos.append(f"Función: ${funcion_latex}$") # Añadir como primer paso

        # 5. Calcular la derivada
        f_prima = diff(f, variable)
        pasos.append(f"Derivada: $f'({variable}) = {latex(f_prima)}$")

        # 6. Elevar la derivada al cuadrado
        f_prima_cuadrada = f_prima**2
        pasos.append(f"Derivada al cuadrado: $[f'({variable})]^2 = {latex(f_prima_cuadrada)}$")

        # 7. Formar el integrando
        integrando = sqrt(1 + f_prima_cuadrada)
        # Usamos \\ para escapar el backslash \ en el f-string de Python para LaTeX
        pasos.append(f"Integrando: $\\sqrt{{1 + {latex(f_prima_cuadrada)}}}$")
        
        # 8. Formar la integral definida completa
        formula_integral = f"L = \\int_{{{a}}}^{{{b}}} {latex(integrando)} d{variable}"
        pasos.append(f"Integral a resolver: ${formula_integral}$")

        # 9. Resolver la integral
        longitud_arco = integrate(integrando, (variable, a, b))
        longitud_arco_num = longitud_arco.evalf() # Valor numérico
        
        pasos.append(f"Resultado exacto: $L = {latex(longitud_arco)}$") # Último paso
        
        # 10. Generar puntos para la gráfica
        # Convertir la expresión de SymPy en una función numérica rápida
        f_numerica = lambdify(variable, f, 'numpy') 
        x_vals = np.linspace(a, b, 100) # 100 puntos para una curva suave
        y_vals = f_numerica(x_vals)

        # Crear formato de puntos {x, y} para Chart.js con eje lineal
        puntos_grafico = [{'x': x_val, 'y': y_val} for x_val, y_val in zip(x_vals, y_vals)]

        # 11. Enviar la respuesta completa como JSON
        return jsonify({
            'success': True,
            'resultado': str(longitud_arco_num), # Resultado numérico como string
            'resultado_exacto': str(longitud_arco), # Resultado simbólico
            'pasos': pasos, # Lista de pasos en formato LaTeX
            'grafico': puntos_grafico, # Datos para el gráfico
            'funcion_latex_display': funcion_latex # LaTeX para la vista previa
        })

    except Exception as e:
        # Manejo de cualquier error durante el cálculo
        return jsonify({
            'success': False,
            'error': f"Error en el cálculo: {str(e)}"
        })

# Iniciar el servidor cuando se ejecuta el script directamente
# Gunicorn usará el objeto 'app', pero esto permite la ejecución local
if __name__ == '__main__':
    # 'host="0.0.0.0"' hace que sea accesible en tu red local (opcional)
    app.run(debug=True, host="0.0.0.0")
