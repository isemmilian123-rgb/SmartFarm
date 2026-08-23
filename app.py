from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

datos = {
    "temperatura": 0,
    "humedad": 0,
    "suelo": 0,
    "riego": False,
    "alerta": "Sistema funcionando correctamente"
}

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        }

        .tarjeta h2 {
            color: #81c784;
        }

        .sensores {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

        .valor {
            font-size: 30px;
            font-weight: bold;
            color: #81c784;
        }

        video {
            width: 100%;
            max-width: 700px;
            background: black;
            border-radius: 12px;
            display: block;
            margin: auto;
        }

        button {
            padding: 12px 20px;
            margin: 10px 5px;
            border: none;
            border-radius: 8px;
            background: #4caf50;
            color: white;
            font-size: 16px;
            cursor: pointer;
        }

        .boton-apagar {
            background: #d32f2f;
        }

        .estado {
            margin: 15px;
            font-size: 18px;
            text-align: center;
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

        .actualizacion {
            text-align: center;
            color: #aaa;
            font-size: 14px;
        }
    </style>
</head>

<body>

<header>
    <h1>🌱 SMART FARM SYSTEM</h1>
    <p>Sistema inteligente de monitoreo agrícola</p>
</header>

<div class="contenedor">

    <div class="tarjeta">
        <h2>📊 Monitoreo del cultivo</h2>

        <div class="sensores">

            <div class="sensor">
                <div class="icono">🌡️</div>
                <h3>Temperatura</h3>
                <div class="valor" id="temperatura">-- °C</div>
            </div>

            <div class="sensor">
                <div class="icono">💧</div>
                <h3>Humedad ambiental</h3>
                <div class="valor" id="humedad">-- %</div>
            </div>

            <div class="sensor">
                <div class="icono">🌱</div>
                <h3>Humedad del suelo</h3>
                <div class="valor" id="suelo">-- %</div>
            </div>

        </div>

        <div class="actualizacion">
            Última actualización:
            <span id="actualizacion">Esperando datos...</span>
        </div>
    </div>

    <div class="tarjeta">

        <h2>🚿 Sistema de riego</h2>

        <div class="riego">

            <div id="estadoRiego" class="riego-apagado">
                🔴 Riego apagado
            </div>

        </div>

    </div>

    <div class="tarjeta">

        <h2>🔔 Estado del sistema</h2>

        <div id="alerta" class="alerta">
            Esperando información del ESP32...
        </div>

    </div>

    <div class="tarjeta">

        <h2>📱 Cámara del teléfono</h2>

        <video id="localVideo" autoplay playsinline muted></video>

        <div style="text-align:center;">

            <button onclick="iniciarCamara()">
                📷 Activar cámara
            </button>

            <button class="boton-apagar" onclick="apagarCamara()">
                ⛔ Apagar cámara
            </button>

        </div>

        <div id="estadoCamara" class="estado">
            Cámara apagada
        </div>

    </div>

</div>

<script>

let stream = null;

async function iniciarCamara() {

    try {

        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: "environment"
            },
            audio: false
        });

        document.getElementById("localVideo").srcObject = stream;

        document.getElementById("estadoCamara").innerHTML =
            "🟢 Cámara del teléfono activada";

    } catch(error) {

        console.error(error);

        document.getElementById("estadoCamara").innerHTML =
            "🔴 No se pudo acceder a la cámara";

    }

}

function apagarCamara() {

    if (stream) {

        stream.getTracks().forEach(function(track) {
            track.stop();
        });

        stream = null;

        document.getElementById("localVideo").srcObject = null;

    }

    document.getElementById("estadoCamara").innerHTML =
        "⚫ Cámara apagada";

}

async function actualizarDatos() {

    try {

        const respuesta = await fetch("/api/datos");

        const datos = await respuesta.json();

        document.getElementById("temperatura").innerHTML =
            datos.temperatura + " °C";

        document.getElementById("humedad").innerHTML =
            datos.humedad + " %";

        document.getElementById("suelo").innerHTML =
            datos.suelo + " %";

        if (datos.riego) {

            document.getElementById("estadoRiego").className =
                "riego-activo";

            document.getElementById("estadoRiego").innerHTML =
                "🟢 Riego activado";

        } else {

            document.getElementById("estadoRiego").className =
                "riego-apagado";

            document.getElementById("estadoRiego").innerHTML =
                "🔴 Riego apagado";

        }

        document.getElementById("alerta").innerHTML =
            datos.alerta;

        document.getElementById("actualizacion").innerHTML =
            new Date().toLocaleTimeString();

    }

    catch(error) {

        console.error(error);

        document.getElementById("alerta").innerHTML =
            "⚠️ No se pueden recibir datos del ESP32";

    }

}

setInterval(actualizarDatos, 3000);

actualizarDatos();

</script>

</body>
</html>
"""

@app.route("/")
def inicio():
    return render_template_string(HTML)


@app.route("/api/datos", methods=["GET"])
def obtener_datos():

    return jsonify(datos)


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


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
