from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit, join_room
import secrets
import string

app = Flask(__name__)

# ============================================================
# SOCKET.IO
# ============================================================

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# ============================================================
# DATOS DEL SISTEMA
# ============================================================

datos = {
    "temperatura": 0,
    "humedad": 0,
    "suelo": 0,
    "riego": False,
    "modo": "automatico",
    "alerta": "Sistema iniciado",
    "automatico_pausado": False
}

# ============================================================
# ORDEN PARA EL ESP32
# ============================================================

orden_riego = {
    "modo": "automatico",
    "riego": False,
    "automatico_pausado": False
}

# ============================================================
# SALAS DE CÁMARA
# ============================================================

salas_camara = {}


def generar_codigo():
    caracteres = string.ascii_uppercase + string.digits

    return "".join(
        secrets.choice(caracteres)
        for _ in range(6)
    )


# ============================================================
# INTERFAZ WEB
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="es">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Smart Farm System</title>

<script src="https://cdn.socket.io/4.8.1/socket.io.min.js"></script>

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
    padding: 22px;
    text-align: center;
}

header h1 {
    margin: 0;
    font-size: 28px;
}

header p {
    margin: 8px 0 0;
}

.contenedor {
    max-width: 950px;
    margin: auto;
    padding: 20px;
}

.tarjeta {
    background: #202820;
    padding: 22px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

h2 {
    margin-top: 0;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}

.dato {
    background: #293329;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
}

.dato .icono {
    font-size: 30px;
}

.dato .valor {
    font-size: 25px;
    font-weight: bold;
    margin-top: 8px;
}

.botones {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
}

button {
    border: none;
    padding: 14px 20px;
    border-radius: 10px;
    color: white;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: 0.85;
}

.btn-auto {
    background: #1976d2;
}

.btn-manual {
    background: #7b1fa2;
}

.btn-regar {
    background: #00897b;
}

.btn-detener {
    background: #c62828;
}

.btn-reactivar {
    background: #388e3c;
}

.btn-camara {
    background: #1565c0;
}

.btn-detener-camara {
    background: #c62828;
}

.btn-cambiar-camara {
    background: #6a1b9a;
}

.estado {
    text-align: center;
    margin-top: 18px;
    padding: 15px;
    border-radius: 10px;
    background: #293329;
    font-size: 18px;
}

.verde {
    color: #66bb6a;
}

.rojo {
    color: #ef5350;
}

.info {
    text-align: center;
    color: #bdbdbd;
    font-size: 14px;
}

.camara-contenedor {
    text-align: center;
}

.video {
    width: 100%;
    max-width: 700px;
    max-height: 500px;
    object-fit: cover;
    background: #000;
    border-radius: 15px;
    margin: 15px auto;
}

#videoCamara {
    display: none;
}

#videoRemoto {
    display: none;
}

.codigo {
    width: 100%;
    max-width: 300px;
    padding: 14px;
    margin: 15px auto;
    border: none;
    border-radius: 10px;
    font-size: 18px;
    text-align: center;
    text-transform: uppercase;
}

.codigo-generado {
    font-size: 30px;
    font-weight: bold;
    letter-spacing: 5px;
    color: #66bb6a;
    margin: 15px;
}

hr {
    border: 0;
    border-top: 1px solid #444;
    margin: 25px 0;
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
     MONITOREO
===================================================== -->

<div class="tarjeta">

<h2>📊 Monitoreo del cultivo</h2>

<div class="grid">

<div class="dato">

<div class="icono">🌡️</div>

<div>Temperatura</div>

<div class="valor" id="temperatura">
-- °C
</div>

</div>

<div class="dato">

<div class="icono">💧</div>

<div>Humedad ambiente</div>

<div class="valor" id="humedad">
-- %
</div>

</div>

<div class="dato">

<div class="icono">🌱</div>

<div>Humedad del suelo</div>

<div class="valor" id="suelo">
-- %
</div>

</div>

<div class="dato">

<div class="icono">🚰</div>

<div>Bomba</div>

<div class="valor" id="riego">
APAGADA
</div>

</div>

</div>

</div>

<!-- =====================================================
     CÁMARA LOCAL
===================================================== -->

<div class="tarjeta">

<h2>📷 Cámara del cultivo</h2>

<div class="camara-contenedor">

<video
id="videoCamara"
class="video"
autoplay
playsinline>
</video>

<div
class="estado"
id="estadoCamara">

📷 Cámara apagada

</div>

<div class="botones">

<button
class="btn-camara"
onclick="activarCamara()">

📷 Activar cámara

</button>

<button
class="btn-detener-camara"
onclick="detenerCamara()">

⏹️ Detener cámara

</button>

<button
class="btn-cambiar-camara"
onclick="cambiarCamara()">

🔄 Cambiar cámara

</button>

</div>

</div>

</div>

<!-- =====================================================
     TRANSMISIÓN TELÉFONO → COMPUTADORA
===================================================== -->

<div class="tarjeta">

<h2>📡 Cámara del cultivo en vivo</h2>

<div class="camara-contenedor">

<h3>📱 Teléfono: transmitir cámara</h3>

<button
class="btn-camara"
onclick="iniciarTransmision()">

📡 Transmitir cámara

</button>

<div
id="codigoMostrar"
style="display:none;">

<p>
Código para conectar la computadora:
</p>

<div
class="codigo-generado"
id="codigoGenerado">

------

</div>

<p class="info">
Mantén esta página abierta en el teléfono.
</p>

</div>

<hr>

<h3>💻 Computadora: ver cámara</h3>

<input
id="codigoSala"
class="codigo"
type="text"
maxlength="6"
placeholder="Código de cámara">

<div class="botones">

<button
class="btn-cambiar-camara"
onclick="verCamara()">

💻 Ver cámara

</button>

<button
class="btn-detener-camara"
onclick="detenerVideoRemoto()">

⏹️ Desconectar

</button>

</div>

<video
id="videoRemoto"
class="video"
autoplay
playsinline
muted>
</video>

<div
class="estado"
id="estadoTransmision">

📡 Cámara sin conexión

</div>

</div>

</div>

<!-- =====================================================
     CONTROL DEL RIEGO
===================================================== -->

<div class="tarjeta">

<h2>🚰 Control del riego</h2>

<div class="botones">

<button
class="btn-auto"
onclick="cambiarModo('automatico')">

🤖 Automático

</button>

<button
class="btn-manual"
onclick="cambiarModo('manual')">

👨‍🌾 Manual

</button>

<button
class="btn-regar"
onclick="controlarRiego('encender')">

💧 Regar

</button>

<button
class="btn-detener"
onclick="controlarRiego('apagar')">

🛑 Detener

</button>

<button
class="btn-reactivar"
onclick="reactivarAutomatico()">

▶️ Reactivar automático

</button>

</div>

<div
class="estado"
id="estado">

Cargando estado...

</div>

</div>

<!-- =====================================================
     ALERTAS
===================================================== -->

<div class="tarjeta">

<h2>📢 Estado del sistema</h2>

<div
class="estado"
id="alerta">

Esperando información...

</div>

<p class="info">
Los datos se actualizan automáticamente.
</p>

</div>

</div>


<script>

// ========================================================
// SOCKET.IO
// ========================================================

const socket = io();


// ========================================================
// VARIABLES DE CÁMARA
// ========================================================

let flujoCamara = null;

let camaraActual = "environment";


// ========================================================
// VARIABLES WEBRTC
// ========================================================

let peerConnection = null;

let salaActual = null;

let soyTransmisor = false;

let candidatosPendientes = [];


// ========================================================
// CONFIGURACIÓN WEBRTC
// ========================================================

const configuracionRTC = {

    iceServers: [

        {
            urls:
            "stun:stun.l.google.com:19302"
        },

        {
            urls:
            "stun:stun1.l.google.com:19302"
        }

    ]

};


// ========================================================
// ACTIVAR CÁMARA
// ========================================================

async function activarCamara() {

    try {

        if (
            !navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia
        ) {

            alert(
                "Este navegador no permite acceder a la cámara."
            );

            return;

        }


        if (flujoCamara) {

            flujoCamara
                .getTracks()
                .forEach(
                    function(track) {
                        track.stop();
                    }
                );

        }


        flujoCamara =
            await navigator.mediaDevices
            .getUserMedia({

                video: {

                    facingMode: {
                        ideal: camaraActual
                    }

                },

                audio: false

            });


        const video =
            document.getElementById(
                "videoCamara"
            );


        video.srcObject =
            flujoCamara;


        video.style.display =
            "block";


        document.getElementById(
            "estadoCamara"
        ).innerText =
            "🟢 Cámara activa";

    }

    catch(error) {

        console.error(
            "Error de cámara:",
            error
        );


        document.getElementById(
            "estadoCamara"
        ).innerText =
            "❌ No se pudo acceder a la cámara";


        alert(
            "No se pudo acceder a la cámara. Verifica los permisos."
        );

    }

}


// ========================================================
// DETENER CÁMARA
// ========================================================

function detenerCamara() {

    if (flujoCamara) {

        flujoCamara
            .getTracks()
            .forEach(
                function(track) {
                    track.stop();
                }
            );

        flujoCamara = null;

    }


    const video =
        document.getElementById(
            "videoCamara"
        );


    video.srcObject = null;

    video.style.display =
        "none";


    document.getElementById(
        "estadoCamara"
    ).innerText =
        "📷 Cámara apagada";

}


// ========================================================
// CAMBIAR CÁMARA
// ========================================================

async function cambiarCamara() {

    if (
        camaraActual ===
        "environment"
    ) {

        camaraActual = "user";

    }

    else {

        camaraActual = "environment";

    }


    if (flujoCamara) {

        await activarCamara();

    }

}


// ========================================================
// CREAR PEER CONNECTION
// ========================================================

function crearPeerConnection() {

    peerConnection =
        new RTCPeerConnection(
            configuracionRTC
        );


    peerConnection.onicecandidate =
        function(event) {

            if (event.candidate) {

                socket.emit(
                    "candidato",
                    {

                        sala: salaActual,

                        candidate:
                            event.candidate

                    }
                );

            }

        };


    peerConnection.ontrack =
        function(event) {

            console.log(
                "🎥 STREAM RECIBIDO"
            );


            const video =
                document.getElementById(
                    "videoRemoto"
                );


            if (
                event.streams &&
                event.streams[0]
            ) {

                video.srcObject =
                    event.streams[0];

                video.style.display =
                    "block";


                video.play()
                .catch(function(error) {

                    console.log(
                        "Autoplay:",
                        error
                    );

                });


                document.getElementById(
                    "estadoTransmision"
                ).innerText =
                    "🟢 Cámara del teléfono conectada";

            }

        };


    peerConnection.onconnectionstatechange =
        function() {

            console.log(
                "WebRTC:",
                peerConnection.connectionState
            );


            if (
                peerConnection.connectionState
                === "connected"
            ) {

                document.getElementById(
                    "estadoTransmision"
                ).innerText =
                    "🟢 Cámara conectada";

            }


            if (
                peerConnection.connectionState
                === "failed"
            ) {

                document.getElementById(
                    "estadoTransmision"
                ).innerText =
                    "❌ No se pudo establecer la conexión";

            }


            if (
                peerConnection.connectionState
                === "disconnected"
            ) {

                document.getElementById(
                    "estadoTransmision"
                ).innerText =
                    "🟡 Cámara desconectada";

            }

        };


    peerConnection.oniceconnectionstatechange =
        function() {

            console.log(
                "ICE:",
                peerConnection.iceConnectionState
            );

        };


    return peerConnection;

}


// ========================================================
// TELÉFONO - INICIAR TRANSMISIÓN
// ========================================================

async function iniciarTransmision() {

    try {

        if (!flujoCamara) {

            camaraActual =
                "environment";

            await activarCamara();

        }


        if (!flujoCamara) {

            return;

        }


        const respuesta =
            await fetch(
                "/api/camara/nueva",
                {
                    method: "POST"
                }
            );


        const resultado =
            await respuesta.json();


        if (
            resultado.estado !== "ok"
        ) {

            alert(
                "No se pudo crear la cámara."
            );

            return;

        }


        salaActual =
            resultado.codigo;


        soyTransmisor =
            true;


        candidatosPendientes = [];


        document.getElementById(
            "codigoGenerado"
        ).innerText =
            salaActual;


        document.getElementById(
            "codigoMostrar"
        ).style.display =
            "block";


        document.getElementById(
            "estadoTransmision"
        ).innerText =
            "🟡 Esperando computadora...";


        socket.emit(
            "crear_sala",
            {
                sala: salaActual
            }
        );

    }

    catch(error) {

        console.error(
            "Error iniciando transmisión:",
            error
        );


        alert(
            "No se pudo iniciar la transmisión."
        );

    }

}


// ========================================================
// COMPUTADORA - VER CÁMARA
// ========================================================

async function verCamara() {

    try {

        const input =
            document.getElementById(
                "codigoSala"
            );


        const codigo =
            input.value
            .trim()
            .toUpperCase();


        if (!codigo) {

            alert(
                "Escribe el código de la cámara."
            );

            return;

        }


        if (peerConnection) {

            peerConnection.close();

            peerConnection = null;

        }


        salaActual =
            codigo;


        soyTransmisor =
            false;


        candidatosPendientes = [];


        crearPeerConnection();


        document.getElementById(
            "estadoTransmision"
        ).innerText =
            "🟡 Conectando con el teléfono...";


        socket.emit(
            "unirse_sala",
            {
                sala: salaActual
            }
        );

    }

    catch(error) {

        console.error(
            "Error conectando:",
            error
        );


        alert(
            "No se pudo conectar con la cámara."
        );

    }

}


// ========================================================
// USUARIO UNIDO
// ========================================================

socket.on(
    "usuario_unido",
    async function() {

        if (!soyTransmisor) {

            return;

        }


        try {

            if (!peerConnection) {

                crearPeerConnection();

            }


            flujoCamara
                .getTracks()
                .forEach(
                    function(track) {

                        peerConnection.addTrack(
                            track,
                            flujoCamara
                        );

                    }
                );


            const oferta =
                await peerConnection
                .createOffer();


            await peerConnection
                .setLocalDescription(
                    oferta
                );


            socket.emit(
                "oferta",
                {

                    sala:
                        salaActual,

                    oferta:
                        peerConnection
                        .localDescription

                }
            );


            document.getElementById(
                "estadoTransmision"
            ).innerText =
                "🟡 Conectando con la computadora...";

        }

        catch(error) {

            console.error(
                "Error creando oferta:",
                error
            );

        }

    }
);


// ========================================================
// RECIBIR OFERTA
// ========================================================

socket.on(
    "oferta",
    async function(data) {

        if (soyTransmisor) {

            return;

        }


        try {

            if (!peerConnection) {

                crearPeerConnection();

            }


            await peerConnection
                .setRemoteDescription(
                    new RTCSessionDescription(
                        data.oferta
                    )
                );


            // Agregar candidatos recibidos
            // antes de crear la respuesta.

            while (
                candidatosPendientes.length > 0
            ) {

                const candidato =
                    candidatosPendientes.shift();


                await peerConnection
                    .addIceCandidate(
                        candidato
                    );

            }


            const respuesta =
                await peerConnection
                .createAnswer();


            await peerConnection
                .setLocalDescription(
                    respuesta
                );


            socket.emit(
                "respuesta",
                {

                    sala:
                        data.sala,

                    respuesta:
                        peerConnection
                        .localDescription

                }
            );

        }

        catch(error) {

            console.error(
                "Error procesando oferta:",
                error
            );

        }

    }
);


// ========================================================
// RECIBIR RESPUESTA
// ========================================================

socket.on(
    "respuesta",
    async function(data) {

        if (!soyTransmisor) {

            return;

        }


        try {

            await peerConnection
                .setRemoteDescription(
                    new RTCSessionDescription(
                        data.respuesta
                    )
                );


            while (
                candidatosPendientes.length > 0
            ) {

                const candidato =
                    candidatosPendientes.shift();


                await peerConnection
                    .addIceCandidate(
                        candidato
                    );

            }

        }

        catch(error) {

            console.error(
                "Error procesando respuesta:",
                error
            );

        }

    }
);


// ========================================================
// RECIBIR ICE
// ========================================================

socket.on(
    "candidato",
    async function(data) {

        try {

            if (!peerConnection) {

                return;

            }


            if (!data.candidate) {

                return;

            }


            const candidato =
                new RTCIceCandidate(
                    data.candidate
                );


            if (
                !peerConnection.remoteDescription
            ) {

                candidatosPendientes.push(
                    candidato
                );

                return;

            }


            await peerConnection
                .addIceCandidate(
                    candidato
                );

        }

        catch(error) {

            console.error(
                "Error ICE:",
                error
            );

        }

    }
);


// ========================================================
// ERROR DE CÁMARA
// ========================================================

socket.on(
    "error_camara",
    function(data) {

        document.getElementById(
            "estadoTransmision"
        ).innerText =
            "❌ " + data.mensaje;


        alert(
            data.mensaje
        );

    }
);


// ========================================================
// DESCONECTAR VIDEO REMOTO
// ========================================================

function detenerVideoRemoto() {

    if (peerConnection) {

        peerConnection.close();

        peerConnection = null;

    }


    const video =
        document.getElementById(
            "videoRemoto"
        );


    video.srcObject = null;

    video.style.display =
        "none";


    candidatosPendientes = [];

    salaActual = null;


    document.getElementById(
        "estadoTransmision"
    ).innerText =
        "📡 Cámara sin conexión";

}


// ========================================================
// OBTENER DATOS
// ========================================================

async function actualizarDatos() {

    try {

        const respuesta =
            await fetch(
                "/api/datos"
            );


        const datos =
            await respuesta.json();


        document.getElementById(
            "temperatura"
        ).innerText =
            Number(
                datos.temperatura
            ).toFixed(1)
            + " °C";


        document.getElementById(
            "humedad"
        ).innerText =
            Number(
                datos.humedad
            ).toFixed(1)
            + " %";


        document.getElementById(
            "suelo"
        ).innerText =
            datos.suelo + " %";


        const bomba =
            document.getElementById(
                "riego"
            );


        if (datos.riego) {

            bomba.innerText =
                "ENCENDIDA";

            bomba.className =
                "valor verde";

        }

        else {

            bomba.innerText =
                "APAGADA";

            bomba.className =
                "valor rojo";

        }


        let textoEstado;


        if (
            datos.modo ===
            "automatico"
        ) {

            textoEstado =
                "🤖 Modo automático";

        }

        else {

            textoEstado =
                "👨‍🌾 Modo manual";

        }


        if (
            datos.automatico_pausado
        ) {

            textoEstado +=
                " | ⏸️ Automático pausado";

        }


        document.getElementById(
            "estado"
        ).innerText =
            textoEstado;


        document.getElementById(
            "alerta"
        ).innerText =
            datos.alerta;

    }

    catch(error) {

        console.log(
            "Error obteniendo datos:",
            error
        );

    }

}


// ========================================================
// CAMBIAR MODO
// ========================================================

async function cambiarModo(modo) {

    try {

        const respuesta =
            await fetch(
                "/api/riego",
                {

                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({

                            accion:
                                "modo",

                            modo:
                                modo

                        })

                }
            );


        const resultado =
            await respuesta.json();


        alert(
            resultado.mensaje
        );


        actualizarDatos();

    }

    catch(error) {

        alert(
            "Error de comunicación"
        );

    }

}


// ========================================================
// REGAR / DETENER
// ========================================================

async function controlarRiego(
    accion
) {

    try {

        const respuesta =
            await fetch(
                "/api/riego",
                {

                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({

                            accion:
                                accion

                        })

                }
            );


        const resultado =
            await respuesta.json();


        if (
            resultado.estado ===
            "error"
        ) {

            alert(
                resultado.mensaje
            );

        }

        else {

            actualizarDatos();

        }

    }

    catch(error) {

        alert(
            "Error de comunicación"
        );

    }

}


// ========================================================
// REACTIVAR AUTOMÁTICO
// ========================================================

async function reactivarAutomatico() {

    try {

        const respuesta =
            await fetch(
                "/api/riego",
                {

                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({

                            accion:
                                "reactivar"

                        })

                }
            );


        const resultado =
            await respuesta.json();


        alert(
            resultado.mensaje
        );


        actualizarDatos();

    }

    catch(error) {

        alert(
            "Error de comunicación"
        );

    }

}


// ========================================================
// ACTUALIZAR CADA 3 SEGUNDOS
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

    return render_template_string(
        HTML
    )


# ============================================================
# CREAR SALA DE CÁMARA
# ============================================================

@app.route(
    "/api/camara/nueva",
    methods=["POST"]
)
def nueva_camara():

    codigo = generar_codigo()

    salas_camara[codigo] = {
        "creada": True
    }

    return jsonify({
        "estado": "ok",
        "codigo": codigo
    })


# ============================================================
# API DATOS - GET
# ============================================================

@app.route(
    "/api/datos",
    methods=["GET"]
)
def obtener_datos():

    datos["automatico_pausado"] = \
        orden_riego["automatico_pausado"]

    return jsonify(datos)


# ============================================================
# API CONTROL DEL RIEGO
# ============================================================

@app.route(
    "/api/riego",
    methods=["POST"]
)
def controlar_riego():

    global datos
    global orden_riego

    try:

        solicitud = request.get_json()

        if not solicitud:

            return jsonify({
                "estado": "error",
                "mensaje":
                    "No se recibieron datos"
            }), 400


        accion = solicitud.get(
            "accion"
        )


        # ====================================================
        # CAMBIAR MODO
        # ====================================================

        if accion == "modo":

            modo = solicitud.get(
                "modo"
            )


            if modo not in [
                "automatico",
                "manual"
            ]:

                return jsonify({
                    "estado": "error",
                    "mensaje":
                        "Modo no válido"
                }), 400


            orden_riego["modo"] = modo

            datos["modo"] = modo

            orden_riego[
                "automatico_pausado"
            ] = False

            orden_riego["riego"] = False

            datos["riego"] = False


            if modo == "automatico":

                datos["alerta"] =
                    "🤖 Riego automático activado"

            else:

                datos["alerta"] =
                    "👨‍🌾 Riego manual activado"


            return jsonify({
                "estado": "ok",
                "mensaje": datos["alerta"]
            })


        # ====================================================
        # ENCENDER
        # ====================================================

        if accion == "encender":

            orden_riego["riego"] = True

            datos["riego"] = True

            datos["alerta"] =
                "💧 Riego activado"


            return jsonify({
                "estado": "ok",
                "mensaje":
                    "💧 Riego activado"
            })


        # ====================================================
        # APAGAR
        # ====================================================

        if accion == "apagar":

            orden_riego["riego"] = False

            datos["riego"] = False


            if (
                orden_riego["modo"]
                == "automatico"
            ):

                orden_riego[
                    "automatico_pausado"
                ] = True

                datos["alerta"] = (
                    "🛑 Riego detenido. "
                    "Automático pausado"
                )

            else:

                datos["alerta"] =
                    "🛑 Riego detenido"


            return jsonify({
                "estado": "ok",
                "mensaje":
                    datos["alerta"]
            })


        # ====================================================
        # REACTIVAR AUTOMÁTICO
        # ====================================================

        if accion == "reactivar":

            orden_riego["modo"] =
                "automatico"

            datos["modo"] =
                "automatico"

            orden_riego[
                "automatico_pausado"
            ] = False

            orden_riego["riego"] = False

            datos["riego"] = False

            datos["alerta"] =
                "▶️ Riego automático reactivado"


            return jsonify({
                "estado": "ok",
                "mensaje":
                    "▶️ Riego automático reactivado"
            })


        return jsonify({
            "estado": "error",
            "mensaje":
                "Acción no válida"
        }), 400


    except Exception as error:

        return jsonify({
            "estado": "error",
            "mensaje": str(error)
        }), 400


# ============================================================
# ESP32 CONSULTA LAS ÓRDENES
# ============================================================

@app.route(
    "/api/riego",
    methods=["GET"]
)
def obtener_orden_riego():

    return jsonify(
        orden_riego
    )


# ============================================================
# ESP32 ENVÍA DATOS
# ============================================================

@app.route(
    "/api/datos",
    methods=["POST"]
)
def recibir_datos():

    global datos

    try:

        nuevos_datos =
            request.get_json()


        if nuevos_datos:

            if "temperatura" in nuevos_datos:

                datos["temperatura"] =
                    nuevos_datos[
                        "temperatura"
                    ]


            if "humedad" in nuevos_datos:

                datos["humedad"] =
                    nuevos_datos[
                        "humedad"
                    ]


            if "suelo" in nuevos_datos:

                datos["suelo"] =
                    nuevos_datos[
                        "suelo"
                    ]


            if "riego" in nuevos_datos:

                datos["riego"] =
                    nuevos_datos[
                        "riego"
                    ]


            if "modo" in nuevos_datos:

                datos["modo"] =
                    nuevos_datos[
                        "modo"
                    ]


        return jsonify({
            "estado": "ok",
            "mensaje":
                "Datos recibidos correctamente"
        })


    except Exception as error:

        return jsonify({
            "estado": "error",
            "mensaje": str(error)
        }), 400


# ============================================================
# SOCKET.IO - CREAR SALA
# ============================================================

@socketio.on("crear_sala")
def crear_sala(data):

    sala = data.get("sala")

    if not sala:
        return

    join_room(sala)

    emit(
        "sala_creada",
        {
            "sala": sala
        },
        to=request.sid
    )


# ============================================================
# SOCKET.IO - UNIRSE A SALA
# ============================================================

@socketio.on("unirse_sala")
def unirse_sala(data):

    sala = data.get("sala")

    if not sala:
        return


    if sala not in salas_camara:

        emit(
            "error_camara",
            {
                "mensaje":
                    "Código de cámara no encontrado."
            },
            to=request.sid
        )

        return


    join_room(sala)


    emit(
        "usuario_unido",
        {},
        to=sala,
        include_self=False
    )


# ============================================================
# SOCKET.IO - OFERTA
# ============================================================

@socketio.on("oferta")
def recibir_oferta(data):

    sala = data.get("sala")

    if sala:

        emit(
            "oferta",
            data,
            to=sala,
            include_self=False
        )


# ============================================================
# SOCKET.IO - RESPUESTA
# ============================================================

@socketio.on("respuesta")
def recibir_respuesta(data):

    sala = data.get("sala")

    if sala:

        emit(
            "respuesta",
            data,
            to=sala,
            include_self=False
        )


# ============================================================
# SOCKET.IO - ICE
# ============================================================

@socketio.on("candidato")
def recibir_candidato(data):

    sala = data.get("sala")

    if sala:

        emit(
            "candidato",
            data,
            to=sala,
            include_self=False
        )


# ============================================================
# SERVIDOR
# ============================================================

if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False
    )
