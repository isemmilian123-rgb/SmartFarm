```python
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ==========================================
# DATOS DEL SISTEMA
# ==========================================

datos = {
    "temperatura": 0,
    "humedad": 0,
    "suelo": 0,
    "riego": False,
    "modo": "automatico",
    "alerta": "Sistema funcionando correctamente"
}

# ==========================================
# ORDEN DE RIEGO
# ==========================================

orden_riego = {
    "modo": "automatico",
    "riego": False
}


# ==========================================
# PAGINA WEB
# ==========================================

HTML = """
<!DOCTYPE html>
<html lang="es">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Smart Farm</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {

            margin: 0;

            font-family: Arial, sans-serif;

            background: #101510;

            color: white;

        }

        header {

            background: #1b5e20;

            padding: 25px 15px;

            text-align: center;

        }

        header h1 {

            margin: 0;

            font-size: 30px;

        }

        header p {

            margin: 8px 0 0;

            color: #d7ffd9;

        }

        .contenedor {

            max-width: 1000px;

            margin: auto;

            padding: 20px;

        }

        .tarjeta {

            background: #202820;

            padding: 20px;

            border-radius: 15px;

            margin-bottom: 20px;

            box-shadow: 0 4px 12px rgba(0,0,0,0.3);

        }

        .tarjeta h2 {

            color: #81c784;

            margin-top: 0;

        }

        .sensores {

            display: grid;

            grid-template-columns:
                repeat(auto-fit, minmax(200px, 1fr));

            gap: 15px;

        }

        .sensor {

            background: #293329;

            padding: 20px;

            border-radius: 12px;

            text-align: center;

        }

        .icono {

            font-size: 35px;

        }

        .sensor h3 {

            margin: 10px 0;

        }

        .valor {

            font-size: 30px;

            font-weight: bold;

            color: #81c784;

        }

        .modo {

            text-align: center;

            padding: 20px;

            background: #293329;

            border-radius: 12px;

            margin-bottom: 15px;

        }

        .modo-actual {

            font-size: 25px;

            font-weight: bold;

            margin-bottom: 15px;

        }

        .automatico {

            color: #81c784;

        }

        .manual {

            color: #64b5f6;

        }

        button {

            padding: 13px 20px;

            margin: 7px;

            border: none;

            border-radius: 8px;

            color: white;

            font-size: 16px;

            cursor: pointer;

        }

        button:hover {

            opacity: 0.85;

        }

        .boton-automatico {

            background: #388e3c;

        }

        .boton-manual {

            background: #1976d2;

        }

        .boton-regar {

            background: #00897b;

        }

        .boton-detener {

            background: #d32f2f;

        }

        .riego {

            text-align: center;

            padding: 20px;

            border-radius: 12px;

            background: #293329;

        }

        .riego-activo {

            color: #4caf50;

            font-size: 25px;

            font-weight: bold;

        }

        .riego-apagado {

            color: #ff5252;

            font-size: 25px;

            font-weight: bold;

        }

        .alerta {

            padding: 15px;

            border-radius: 10px;

            background: #263b27;

            color: #b9f6ca;

            font-size: 18px;

            text-align: center;

        }

        video {

            width: 100%;

            max-width: 700px;

            background: black;

            border-radius: 12px;

            display: block;

            margin: auto;

        }

        .estado {

            margin: 15px;

            font-size: 18px;

            text-align: center;

        }

        .actualizacion {

            text-align: center;

            color: #aaa;

            font-size: 14px;

            margin-top: 10px;

        }

        footer {

            text-align: center;

            padding: 20px;

            color: #888;

        }

    </style>

</head>


<body>


<header>

    <h1>🌱 SMART FARM SYSTEM</h1>

    <p>
        Sistema inteligente de monitoreo agrícola
    </p>

</header>


<div class="contenedor">


    <!-- =================================
         SENSORES
    ================================== -->

    <div class="tarjeta">

        <h2>📊 Monitoreo del cultivo</h2>

        <div class="sensores">


            <div class="sensor">

                <div class="icono">🌡️</div>

                <h3>Temperatura</h3>

                <div
                    class="valor"
                    id="temperatura">
                    -- °C
                </div>

            </div>


            <div class="sensor">

                <div class="icono">💧</div>

                <h3>Humedad ambiental</h3>

                <div
                    class="valor"
                    id="humedad">
                    -- %
                </div>

            </div>


            <div class="sensor">

                <div class="icono">🌱</div>

                <h3>Humedad del suelo</h3>

                <div
                    class="valor"
                    id="suelo">
                    -- %
                </div>

            </div>


        </div>


        <div class="actualizacion">

            Última actualización:

            <span id="actualizacion">
                Esperando datos...
            </span>

        </div>

    </div>



    <!-- =================================
         CONTROL DE RIEGO
    ================================== -->

    <div class="tarjeta">

        <h2>🚿 Control de riego</h2>


        <div class="modo">

            <div
                id="modoActual"
                class="modo-actual automatico">

                🤖 Modo automático

            </div>


            <button
                class="boton-automatico"
                onclick="cambiarModo('automatico')">

                🤖 Automático

            </button>


            <button
                class="boton-manual"
                onclick="cambiarModo('manual')">

                👨‍🌾 Manual

            </button>


            <br>


            <button
                class="boton-regar"
                onclick="regarAhora()">

                💧 Regar ahora

            </button>


            <button
                class="boton-detener"
                onclick="detenerRiego()">

                🛑 Detener riego

            </button>

        </div>


        <div class="riego">

            <div
                id="estadoRiego"
                class="riego-apagado">

                🔴 Riego apagado

            </div>

        </div>

    </div>



    <!-- =================================
         ALERTAS
    ================================== -->

    <div class="tarjeta">

        <h2>🔔 Estado del sistema</h2>

        <div
            id="alerta"
            class="alerta">

            Esperando información del ESP32...

        </div>

    </div>



    <!-- =================================
         CAMARA
    ================================== -->

    <div class="tarjeta">

        <h2>📱 Cámara del teléfono</h2>


        <video
            id="localVideo"
            autoplay
            playsinline
            muted>
        </video>


        <div style="text-align:center;">


            <button
                class="boton-automatico"
                onclick="iniciarCamara()">

                📷 Activar cámara

            </button>


            <button
                class="boton-detener"
                onclick="apagarCamara()">

                ⛔ Apagar cámara

            </button>


        </div>


        <div
            id="estadoCamara"
            class="estado">

            Cámara apagada

        </div>

    </div>


</div>


<footer>

    🌱 Smart Farm System © 2026

</footer>



<script>


// ==========================================
// CAMARA
// ==========================================

let stream = null;


async function iniciarCamara() {

    try {

        stream =
            await navigator.mediaDevices.getUserMedia({

                video: {
                    facingMode: "environment"
                },

                audio: false

            });


        document
            .getElementById("localVideo")
            .srcObject = stream;


        document
            .getElementById("estadoCamara")
            .innerHTML =
            "🟢 Cámara del teléfono activada";


    }

    catch(error) {

        console.error(error);


        document
            .getElementById("estadoCamara")
            .innerHTML =
            "🔴 No se pudo acceder a la cámara";

    }

}


function apagarCamara() {


    if (stream) {


        stream
            .getTracks()
            .forEach(function(track) {

                track.stop();

            });


        stream = null;


        document
            .getElementById("localVideo")
            .srcObject = null;

    }


    document
        .getElementById("estadoCamara")
        .innerHTML =
        "⚫ Cámara apagada";

}



// ==========================================
// CAMBIAR MODO
// ==========================================

async function cambiarModo(modo) {


    try {


        const respuesta =
            await fetch("/api/riego", {

                method: "POST",

                headers: {
                    "Content-Type":
                    "application/json"
                },

                body: JSON.stringify({

                    accion: "modo",

                    modo: modo

                })

            });


        const resultado =
            await respuesta.json();


        actualizarModo(modo);


        document
            .getElementById("alerta")
            .innerHTML =
            resultado.mensaje;


    }

    catch(error) {

        console.error(error);

        document
            .getElementById("alerta")
            .innerHTML =
            "⚠️ No se pudo cambiar el modo";

    }

}



// ==========================================
// REGAR AHORA
// ==========================================

async function regarAhora() {


    try {


        const respuesta =
            await fetch("/api/riego", {

                method: "POST",

                headers: {
                    "Content-Type":
                    "application/json"
                },

                body: JSON.stringify({

                    accion: "encender"

                })

            });


        const resultado =
            await respuesta.json();


        document
            .getElementById("alerta")
            .innerHTML =
            resultado.mensaje;


    }

    catch(error) {

        console.error(error);

        document
            .getElementById("alerta")
            .innerHTML =
            "⚠️ No se pudo activar el riego";

    }

}



// ==========================================
// DETENER RIEGO
// ==========================================

async function detenerRiego() {


    try {


        const respuesta =
            await fetch("/api/riego", {

                method: "POST",

                headers: {
                    "Content-Type":
                    "application/json"
                },

                body: JSON.stringify({

                    accion: "apagar"

                })

            });


        const resultado =
            await respuesta.json();


        document
            .getElementById("alerta")
            .innerHTML =
            resultado.mensaje;


    }

    catch(error) {

        console.error(error);

        document
            .getElementById("alerta")
            .innerHTML =
            "⚠️ No se pudo detener el riego";

    }

}



// ==========================================
// ACTUALIZAR MODO VISUAL
// ==========================================

function actualizarModo(modo) {


    const elemento =
        document.getElementById("modoActual");


    if (modo === "manual") {

        elemento.className =
            "modo-actual manual";

        elemento.innerHTML =
            "👨‍🌾 Modo manual";

    }

    else {

        elemento.className =
            "modo-actual automatico";

        elemento.innerHTML =
            "🤖 Modo automático";

    }

}



// ==========================================
// ACTUALIZAR DATOS
// ==========================================

async function actualizarDatos() {


    try {


        const respuesta =
            await fetch("/api/datos");


        const datos =
            await respuesta.json();


        document
            .getElementById("temperatura")
            .innerHTML =
            datos.temperatura + " °C";


        document
            .getElementById("humedad")
            .innerHTML =
            datos.humedad + " %";


        document
            .getElementById("suelo")
            .innerHTML =
            datos.suelo + " %";


        actualizarModo(datos.modo);


        if (datos.riego) {


            document
                .getElementById("estadoRiego")
                .className =
                "riego-activo";


            document
                .getElementById("estadoRiego")
                .innerHTML =
                "🟢 Riego activado";

        }

        else {


            document
                .getElementById("estadoRiego")
                .className =
                "riego-apagado";


            document
                .getElementById("estadoRiego")
                .innerHTML =
                "🔴 Riego apagado";

        }


        document
            .getElementById("alerta")
            .innerHTML =
            datos.alerta;


        document
            .getElementById("actualizacion")
            .innerHTML =
            new Date().toLocaleTimeString();


    }


    catch(error) {


        console.error(error);


        document
            .getElementById("alerta")
            .innerHTML =
            "⚠️ No se pueden recibir datos del ESP32";

    }

}



// Actualizar cada 3 segundos

setInterval(actualizarDatos, 3000);

actualizarDatos();


</script>


</body>

</html>
"""


# ==========================================
# PAGINA PRINCIPAL
# ==========================================

@app.route("/")
def inicio():

    return render_template_string(HTML)



# ==========================================
# API: DATOS
# ==========================================

@app.route("/api/datos", methods=["GET"])
def obtener_datos():
    return jsonify(datos)


# ==========================================
# API: CONTROL DEL RIEGO
# ==========================================

@app.route("/api/riego", methods=["POST"])
def controlar_riego():

    global datos
    global orden_riego

    try:

        solicitud = request.get_json()
        accion = solicitud.get("accion")

        # CAMBIAR MODO
        if accion == "modo":

            modo = solicitud.get("modo")

            if modo not in ["automatico", "manual"]:
                return jsonify({
                    "estado": "error",
                    "mensaje": "Modo no válido"
                }), 400

            orden_riego["modo"] = modo
            datos["modo"] = modo

            if modo == "automatico":
                datos["alerta"] = "🤖 Riego automático activado"
            else:
                datos["alerta"] = "👨‍🌾 Riego manual activado"

            return jsonify({
                "estado": "ok",
                "mensaje": datos["alerta"]
            })


        # ENCENDER BOMBA
        if accion == "encender":

            orden_riego["riego"] = True
            datos["riego"] = True
            datos["alerta"] = "💧 Riego activado manualmente"

            return jsonify({
                "estado": "ok",
                "mensaje": "💧 Riego activado"
            })


        # APAGAR BOMBA
        if accion == "apagar":

            orden_riego["riego"] = False
            datos["riego"] = False
            datos["alerta"] = "🛑 Riego detenido"

            return jsonify({
                "estado": "ok",
                "mensaje": "🛑 Riego detenido"
            })


        return jsonify({
            "estado": "error",
            "mensaje": "Acción no válida"
        }), 400


    except Exception as error:

        return jsonify({
            "estado": "error",
            "mensaje": str(error)
        }), 400


# ==========================================
# API: EL ESP32 CONSULTA LAS ORDENES
# ==========================================

@app.route("/api/riego", methods=["GET"])
def obtener_orden_riego():

    return jsonify(orden_riego)


# ==========================================
# RECIBIR DATOS DEL ESP32
# ==========================================

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


# ==========================================
# INICIAR SERVIDOR
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

