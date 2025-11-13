# app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sympy import sympify, diff, sqrt, integrate, symbols, lambdify, latex
import numpy as np
import os

# --- Configuración del Directorio (para Render) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, '.')

app = Flask(__name__, static_folder=None)
CORS(app)

# --- RUTA PARA SERVIR LA PÁGINA WEB (index.html) ---
@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

# --- RUTA PARA LA API DE CÁLCULO ---
@app.route('/calcular', methods=['POST'])
def calcular_longitud_arco():
    datos = request.json
    funcion_str = datos['funcion']
    a_str = datos['limite_a']
    b_str = datos['limite_b']
    
    pasos = []
    try:
        a = float(a_str)
        b = float(b_str)

        f = sympify(funcion_str)
        variables = f.free_symbols
        
        if len(variables) > 1:
            raise Exception(f"La función debe tener solo una variable, pero se encontraron: {variables}")
        elif len(variables) == 0:
            variable = symbols('x')
        else:
            variable = variables.pop()

        funcion_latex = f"f({variable}) = {latex(f)}"
        pasos.append(f"Función: ${funcion_latex}$")

        f_prima = diff(f, variable)
        pasos.append(f"Derivada: $f'({variable}) = {latex(f_prima)}$")

        f_prima_cuadrada = f_prima**2
        pasos.append(f"Derivada al cuadrado: $[f'({variable})]^2 = {latex(f_prima_cuadrada)}$")

        integrando = sqrt(1 + f_prima_cuadrada)
        pasos.append(f"Integrando: $\\sqrt{{1 + {latex(f_prima_cuadrada)}}}$")
        
        formula_integral = f"L = \\int_{{{a}}}^{{{b}}} {latex(integrando)} d{variable}"
        pasos.append(f"Integral a resolver: ${formula_integral}$")

        longitud_arco = integrate(integrando, (variable, a, b))
        longitud_arco_num = longitud_arco.evalf()
        pasos.append(f"Resultado exacto: $L = {latex(longitud_arco)}$")
        
        # --- LÓGICA DE GRÁFICO MODIFICADA ---
        f_numerica = lambdify(variable, f, 'numpy')
        
        # 1. Datos para el ÁREA SOMBREADA (solo el intervalo [a, b])
        x_vals_area = np.linspace(a, b, 100)
        y_vals_area = f_numerica(x_vals_area)
        # Filtramos valores NaN (Not a Number) por si hay errores de dominio (ej. sqrt(-1))
        puntos_area = [{'x': x, 'y': y} for x, y in zip(x_vals_area, y_vals_area) if not np.isnan(y)]

        # 2. Datos para la LÍNEA (intervalo con márgenes)
        longitud_intervalo = b - a
        # Añadimos un 20% de relleno a cada lado
        padding = longitud_intervalo * 0.20
        
        # Manejo especial si el intervalo es 0 (un solo punto)
        if padding == 0:
            padding = 1.0 # Añade un relleno de 1 a cada lado

        a_grafico = a - padding
        b_grafico = b + padding
        
        x_vals_linea = np.linspace(a_grafico, b_grafico, 150) # Más puntos para una línea suave
        y_vals_linea = f_numerica(x_vals_linea)
        puntos_linea = [{'x': x, 'y': y} for x, y in zip(x_vals_linea, y_vals_linea) if not np.isnan(y)]

        # --- Respuesta JSON actualizada ---
        return jsonify({
            'success': True,
            'resultado': str(longitud_arco_num),
            'resultado_exacto': str(longitud_arco),
            'pasos': pasos,
            'grafico_area': puntos_area, # Datos solo del área
            'grafico_linea': puntos_linea, # Datos de la línea extendida
            'funcion_latex_display': funcion_latex
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error en el cálculo: {str(e)}"
        })

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
