# app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sympy import sympify, diff, sqrt, integrate, symbols, lambdify, latex
import numpy as np

# Inicializar la aplicación Flask
app = Flask(__name__)
# Configurar CORS para permitir peticiones desde el frontend
CORS(app)

# --- ¡NUEVA RUTA PARA SERVIR LA PÁGINA WEB! ---
@app.route('/')
def index():
    # Esta línea le dice a Flask que envíe el archivo 'index.html'
    # cuando alguien visite la raíz de tu sitio web.
    return send_from_directory('.', 'index.html')

@app.route('/calcular', methods=['POST'])
def calcular_longitud_arco():
    # 1. Obtener los datos JSON enviados desde el frontend
    datos = request.json
    funcion_str = datos['funcion']
    a_str = datos['limite_a']
    b_str = datos['limite_b']
    
    pasos = []
    try:
        # 2. Convertir límites a números
        a = float(a_str)
        b = float(b_str)

        # 3. Detectar la variable automáticamente (x, y, z, etc.)
        f = sympify(funcion_str) # Convertir el string a una expresión SymPy
        
        variables = f.free_symbols
        
        if len(variables) > 1:
            raise Exception(f"La función debe tener solo una variable, pero se encontraron: {variables}")
        elif len(variables) == 0:
            variable = symbols('x') # Usar 'x' por defecto si es una constante (ej: "5")
        else:
            variable = variables.pop() # Obtener la variable encontrada (ej: 'y' o 'z')

        # 4. Generar el LaTeX para la función principal
        funcion_latex = f"f({variable}) = {latex(f)}"
        pasos.append(f"Función: ${funcion_latex}$")

        # 5. Calcular la derivada (usando la variable detectada)
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
        
        pasos.append(f"Resultado exacto: $L = {latex(longitud_arco)}$")
        
        # 10. Generar puntos para la gráfica
        f_numerica = lambdify(variable, f, 'numpy')
        x_vals = np.linspace(a, b, 100) # 100 puntos para una curva suave
        y_vals = f_numerica(x_vals)

        # Formato de puntos {x, y} para Chart.js con eje lineal
        puntos_grafico = [{'x': x_val, 'y': y_val} for x_val, y_val in zip(x_vals, y_vals)]

        # 11. Enviar la respuesta completa como JSON
        return jsonify({
            'success': True,
            'resultado': str(longitud_arco_num),
            'resultado_exacto': str(longitud_arco),
            'pasos': pasos,
            'grafico': puntos_grafico,
            'funcion_latex_display': funcion_latex # Enviamos el LaTeX de la función por separado
        })

    except Exception as e:
        # Manejo de cualquier error durante el cálculo
        return jsonify({
            'success': False,
            'error': f"Error en el cálculo: {str(e)}"
        })

# Iniciar el servidor cuando se ejecuta el script
if __name__ == '__main__':

    app.run(debug=True)