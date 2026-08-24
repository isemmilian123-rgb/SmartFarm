from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)


# ============================================================
# ESTADO DEL SISTEMA
# ============================================================

datos = {
    "temperatura": 0,
    "humedad": 0,
    "suelo": 0,
    "riego": False,
    "modo": "automatico",
    "alerta": "Sistema iniciado"
}


# ============================================================
# ORDEN PARA EL ESP32
# ============================================================

orden_riego = {
    "modo": "automatico",
    "riego": False
}


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Smart Farm</title>

<style>

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #101510;
    color: white;
    text-align: center;
}

header {
    background: #1b5e20;
    padding: 20px;
}

.contenedor {
    max-width: 900px;
    margin: 20px auto;
    padding: 20px;
}

.tarjeta {
    background: #202820;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
}

.dato {
    font-size: 24px;
    margin: 15px;
}

button {
    padding: 12px 20px;
    margin: 8px;
    border: none;
    border-radius: 8px;
    color: white;
    font-size: 16px;
    cursor: pointer;
}

.automatico {
    background: #388e3c;
}

.manual {
    background: #1976d2;
}

.regar {
    background: #009688;
}

.detener {
    background: #c62828;
}

.estado {
    font-size: 20px;
    margin: 15px;
}

.verde {
    color: #4caf50;
}

.rojo {
    color: #ff5252;
}

</style>

</head>


<body>


<header>

<h1>🌱 SMART FARM SYSTEM</h1>

<p>Sistema inteligente de monitoreo agrícola</p>

</header>


<div class="contenedor">


<!-- =====================================================
     SENSORES
====================================================== -->

<div class="tarjeta">

<h2>📊 Datos del cultivo</h2>

<div class="dato">
🌡️ Temperatura:
<span id="temperatura">--</span> °C
</div>

<div class="dato">
💧 Humedad ambiental:
<span id="humedad">--</span> %
</div>

<div class="dato">
🌱 Humedad del suelo:
<span id="suelo">--</span> %
</div>

<div class="dato">
🚿 Bomba:
<span id="riego">--</span>
</div>

<div class="estado">
Estado:
<span id="alerta">Esperando datos...</span>
</div>

</div>


<!-- =====================================================
     CONTROL DEL RIEGO
====================================================== -->

<div class="tarjeta">

<h2>🚿 Control del riego</h2>

<p>
Modo actual:
<strong id="modo">--</strong>
</p>


<button
class="automatico"
onclick="cambiarModo('automatico')">

🤖 Modo automático

</button>


<button
class="manual"
onclick="cambiarModo('manual')">

👨‍🌾 Modo manual

</button>


<br>


<button
class="regar"
onclick="controlarRiego('encender')">

💧 Regar ahora

</button>


<button
class="detener"
onclick="controlarRiego('apagar')">

🛑 Detener riego

</button>


</div>


</div>


<script>


// ========================================================
// OBTENER DATOS
// ========================================================

async function actualizarDatos() {

    try {

        const respuesta =
            await fetch('/api/datos');

        const datos =
            await respuesta.json();


        document.getElementById('temperatura')
            .innerText =
            datos.temperatura;


        document.getElementById('humedad')
            .innerText =
            datos.humedad;


        document.getElementById('suelo')
            .innerText =
            datos.suelo;


        document.getElementById('modo')
            .innerText =
            datos.modo;


        if (datos.riego) {

            document.getElementById('riego')
                .innerHTML =
                '<span class="verde">ENCENDIDA</span>';

        } else {

            document.getElementById('riego')
                .innerHTML =
                '<span class="rojo">APAGADA</span>';

        }


        document.getElementById('alerta')
            .innerText =
            datos.alerta;


    } catch(error) {

        console.log(error);

    }

}


// ========================================================
// CAMBIAR MODO
// ========================================================

async function cambiarModo(modo) {

    try {

        const respuesta =
            await fetch('/api/riego', {

                method: 'POST',

                headers: {
                    'Content-Type':
                    'application/json'
                },

                body: JSON.stringify({

                    accion: 'modo',

                    modo: modo

                })

            });


        const resultado =
            await respuesta.json();


        alert(resultado.mensaje);


        actualizarDatos();


    } catch(error) {

        alert(
            'Error al cambiar el modo'
        );

    }

}


// ========================================================
// CONTROL DE BOMBA
// ========================================================

async function controlarRiego(accion) {

    try {

        const respuesta =
            await fetch('/api/riego', {

                method: 'POST',

                headers: {
                    'Content-Type':
                    'application/json'
                },

                body: JSON.stringify({

                    accion: accion

                })

            });


        const resultado =
            await respuesta.json();


        alert(resultado.mensaje);


        actualizarDatos();


    } catch(error) {

        alert(
            'Error controlando el riego'
        );

    }

}


// ========================================================
// ACTUALIZAR AUTOMÁTICAMENTE
// ========================================================

actualizarDatos();

setInterval(
    actualizarDatos,
    3000
);


</script>


</body>

</html>
"""


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def inicio():
    return render_template_string(HTML)


# ============================================================
# API DATOS - GET
# ============================================================

@app.route("/api/datos", methods=["GET"])
def obtener_datos():
    return jsonify(datos)


# ============================================================
# API CONTROL DEL RIEGO
# ============================================================

@app.route("/api/riego", methods=["POST"])
def controlar_riego():

    global datos
    global orden_riego

    try:

        solicitud = request.get_json()
        accion = solicitud.get("accion")

        # ----------------------------------------------------
        # CAMBIAR MODO
        # ----------------------------------------------------

        if accion == "modo":

            modo = solicitud.get("modo")

            if modo not in ["automatico", "manual"]:

                return jsonify({
                    "estado": "error",
                    "mensaje": "Modo no válido"
                }), 400

            orden_riego["modo"] = modo
            datos["modo"] = modo

            # Al cambiar de modo se apaga cualquier
            # orden anterior de riego.

            orden_riego["riego"] = False
            datos["riego"] = False

            if modo == "automatico":

                datos["alerta"] = "🤖 Riego automático activado"

            else:

                datos["alerta"] = "👨‍🌾 Riego manual activado"

            return jsonify({
                "estado": "ok",
                "mensaje": datos["alerta"]
            })

        # ----------------------------------------------------
        # ENCENDER BOMBA
        # ----------------------------------------------------

        if accion == "encender":

            # Solo se permite encender manualmente
            # cuando el sistema está en modo manual.

            if orden_riego["modo"] != "manual":

                return jsonify({
                    "estado": "error",
                    "mensaje": "Cambia primero a modo manual"
                }), 400

            orden_riego["riego"] = True
            datos["riego"] = True
            datos["alerta"] = "💧 Riego manual activado"

            return jsonify({
                "estado": "ok",
                "mensaje": "💧 Riego activado"
            })

        # ----------------------------------------------------
        # APAGAR BOMBA
        # ----------------------------------------------------

        if accion == "apagar":

            orden_riego["riego"] = False
            datos["riego"] = False
            datos["alerta"] = "🛑 Riego detenido"

            return jsonify({
                "estado": "ok",
                "mensaje": "🛑 Riego detenido"
            })

        # ----------------------------------------------------
        # ACCIÓN NO VÁLIDA
        # ----------------------------------------------------

        return jsonify({
            "estado": "error",
            "mensaje": "Acción no válida"
        }), 400

    except Exception as error:

        return jsonify({
            "estado": "error",
            "mensaje": str(error)
        }), 400


# ============================================================
# ESP32 CONSULTA LAS ÓRDENES
# ============================================================

@app.route("/api/riego", methods=["GET"])
def obtener_orden_riego():

    return jsonify(orden_riego)


# ============================================================
# ESP32 ENVÍA DATOS
# ============================================================

@app.route("/api/datos", methods=["POST"])
def recibir_datos():

    global datos

    try:

        nuevos_datos = request.get_json()

        if nuevos_datos:

            if "temperatura" in nuevos_datos:
                datos["temperatura"] = nuevos_datos["temperatura"]

            if "humedad" in nuevos_datos:
                datos["humedad"] = nuevos_datos["humedad"]

            if "suelo" in nuevos_datos:
                datos["suelo"] = nuevos_datos["suelo"]

            if "riego" in nuevos_datos:
                datos["riego"] = nuevos_datos["riego"]

            if "alerta" in nuevos_datos:
                datos["alerta"] = nuevos_datos["alerta"]

        return jsonify({
            "estado": "ok",
            "mensaje": "Datos recibidos correctamente"
        })

    except Exception as error:

        return jsonify({
            "estado": "error",
            "mensaje": str(error)
        }), 400


# ============================================================
# SERVIDOR
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
