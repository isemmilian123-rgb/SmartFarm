from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

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

        video {
            width: 100%;
            max-width: 700px;
            background: black;
            border-radius: 12px;
        }

        button {
            padding: 12px 20px;
            margin: 10px;
            border: none;
            border-radius: 8px;
            background: #4caf50;
            color: white;
            font-size: 16px;
        }

        .estado {
            margin: 15px;
            font-size: 18px;
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

        <h2>📱 Cámara del teléfono</h2>

        <video id="localVideo" autoplay playsinline muted></video>

        <br>

        <button onclick="iniciarCamara()">
            📷 Activar cámara
        </button>

        <div id="estado" class="estado">
            Cámara apagada
        </div>

    </div>


    <div class="tarjeta">

        <h2>💻 Vista de la cámara</h2>

        <video id="remoteVideo" autoplay playsinline></video>

        <p>
            Esta será la vista que posteriormente verá la computadora.
        </p>

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

        document.getElementById("estado").innerHTML =
            "🟢 Cámara del teléfono activada";

    } catch(error) {

        console.error(error);

        document.getElementById("estado").innerHTML =
            "🔴 Error al acceder a la cámara";

    }

}

</script>

</body>
</html>
"""

@app.route("/")
def inicio():
    return render_template_string(HTML)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        ssl_context="adhoc"
    )