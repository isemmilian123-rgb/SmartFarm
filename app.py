import base64
import io
import secrets
import string

from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit, join_room

from PIL import Image, ImageChops, ImageStat


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Flask(__name__)

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

orden_riego = {
    "modo": "automatico",
    "riego": False,
    "automatico_pausado": False
}

salas_camara = {}

# Imagen utilizada como referencia para el análisis
imagen_anterior = None


# ============================================================
# GENERAR CÓDIGO DE CÁMARA
# ============================================================

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

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Smart Farm System</title>

<script
    src="https://cdn.socket.io/4.8.1/socket.io.min.js">
</script>

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

.btn-analizar {
    background: #ef6c00;
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

#videoCamara,
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

    <h1>
        🌱 SMART FARM SYSTEM
    </h1>

    <p>
        Sistema inteligente de monitoreo agrícola
    </p>

</header>


<div class="contenedor">


<!-- ========================================================
     MONITOREO
     ======================================================== -->

<div class="tarjeta">

    <h2>
        📊 Monitoreo del cultivo
    </h2>

    <div class="grid">


        <div class="dato">

            <div class="icono">
                🌡️
            </div>

            <div>
                Temperatura
            </div>

            <div
                class="valor"
                id="temperatura"
            >
                -- °C
            </div>

        </div>


        <div class="dato">

            <div class="icono">
                💧
            </div>

            <div>
                Humedad ambiente
            </div>

            <div
                class="valor"
                id="humedad"
            >
                -- %
            </div>

        </div>


        <div class="dato">

            <div class="icono">
                🌱
            </div>

            <div>
                Humedad del suelo
            </div>

            <div
                class="valor"
                id="suelo"
            >
                -- %
            </div>

        </div>


        <div class="dato">

            <div class="icono">
                🚰
            </div>

            <div>
                Bomba
            </div>

            <div
                class="valor"
                id="riego"
            >
                APAGADA
            </div>

        </div>


    </div>

</div>


<!-- ========================================================
     CÁMARA LOCAL
     ======================================================== -->

<div class="tarjeta">

    <h2>
        📷 Cámara del cultivo
    </h2>

    <div class="camara-contenedor">


        <video
            id="videoCamara"
            class="video"
            autoplay
            playsinline
        ></video>


        <div
            class="estado"
            id="estadoCamara"
        >
            📷 Cámara apagada
        </div>


        <div class="botones">


            <button
                class="btn-camara"
                onclick="activarCamara()"
            >
                📷 Activar cámara
            </button>


            <button
                class="btn-detener-camara"
                onclick="detenerCamara()"
            >
                ⏹️ Detener cámara
            </button>


            <button
                class="btn-cambiar-camara"
                onclick="cambiarCamara()"
            >
                🔄 Cambiar cámara
            </button>


        </div>

    </div>

</div>


<!-- ========================================================
     TRANSMISIÓN DEL TELÉFONO
     ======================================================== -->

<div class="tarjeta">

    <h2>
        📡 Cámara del cultivo en vivo
    </h2>


    <div class="camara-contenedor">


        <h3>
            📱 Teléfono: transmitir cámara
        </h3>


        <button
            class="btn-camara"
            onclick="iniciarTransmision()"
        >
            📡 Transmitir cámara
        </button>


        <div
            id="codigoMostrar"
            style="display:none;"
        >

            <p>
                Código para conectar la computadora:
            </p>


            <div
                class="codigo-generado"
                id="codigoGenerado"
            >
                ------
            </div>


            <p class="info">
                Mantén esta página abierta en el teléfono.
            </p>

        </div>


        <hr>


        <h3>
            💻 Computadora: ver cámara
        </h3>


        <input
            id="codigoSala"
            class="codigo"
            type="text"
            maxlength="6"
            placeholder="Código de cámara"
        >


        <div class="botones">


            <button
                class="btn-cambiar-camara"
                onclick="verCamara()"
            >
                💻 Ver cámara
            </button>


            <button
                class="btn-detener-camara"
                onclick="detenerVideoRemoto()"
            >
                ⏹️ Desconectar
            </button>


        </div>


        <video
            id="videoRemoto"
            class="video"
            autoplay
            playsinline
            muted
        ></video>


        <div
            class="estado"
            id="estadoTransmision"
        >
            📡 Cámara sin conexión
        </div>


        <!-- ==================================================
             DETECCIÓN DE ANOMALÍAS
             ================================================== -->

        <div class="tarjeta">

            <h2>
                🔍 Detección de anomalías
            </h2>


            <p class="info">
                El sistema compara imágenes del cultivo
                para detectar cambios visuales.
            </p>


            <div class="botones">

                <button
                    class="btn-analizar"
                    onclick="analizarCultivo()"
                >
                    🔍 Analizar cultivo
                </button>

            </div>


            <div
                class="estado"
                id="resultadoAnalisis"
            >
                🔍 Esperando análisis...
            </div>

        </div>


    </div>

</div>


<!-- ========================================================
     CONTROL DE RIEGO
     ======================================================== -->

<div class="tarjeta">

    <h2>
        🚰 Control del riego
    </h2>


    <div class="botones">


        <button
            class="btn-auto"
            onclick="cambiarModo('automatico')"
        >
            🤖 Automático
        </button>


        <button
            class="btn-manual"
            onclick="cambiarModo('manual')"
        >
            👨‍🌾 Manual
        </button>


        <button
            class="btn-regar"
            onclick="controlarRiego('encender')"
        >
            💧 Regar
        </button>


        <button
            class="btn-detener"
            onclick="controlarRiego('apagar')"
        >
            🛑 Detener
        </button>


        <button
            class="btn-reactivar"
            onclick="reactivarAutomatico()"
        >
            ▶️ Reactivar automático
        </button>


    </div>


    <div
        class="estado"
        id="estado"
    >
        Cargando estado...
    </div>

</div>


<!-- ========================================================
     ESTADO DEL SISTEMA
     ======================================================== -->

<div class="tarjeta">

    <h2>
        📢 Estado del sistema
    </h2>


    <div
        class="estado"
        id="alerta"
    >
        Esperando información...
    </div>


    <p class="info">
        Los datos se actualizan automáticamente.
    </p>

</div>


</div>


<script>

// ============================================================
// SOCKET.IO
// ============================================================

const socket = io();


// ============================================================
// VARIABLES DE CÁMARA
// ============================================================

let flujoCamara = null;

let camaraActual = "environment";

let peerConnection = null;

let salaActual = null;

let soyTransmisor = false;

let candidatosPendientes = [];


// ============================================================
// CONFIGURACIÓN WEBRTC
// ============================================================

const configuracionRTC = {

    iceServers: [

        {
            urls: "stun:stun.l.google.com:19302"
        },

        {
            urls: "stun:stun1.l.google.com:19302"
        }

    ]

};


// ============================================================
// ACTIVAR CÁMARA
// ============================================================

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
                    track => track.stop()
                );

        }


        flujoCamara =
            await navigator.mediaDevices.getUserMedia({

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


    } catch (error) {

        console.error(
            "Error de cámara:",
            error
        );


        document.getElementById(
            "estadoCamara"
        ).innerText =
            "❌ No se pudo acceder a la cámara";


        alert(
            "No se pudo acceder a la cámara. " +
            "Verifica los permisos."
        );

    }

}


// ============================================================
// DETENER CÁMARA
// ============================================================

function detenerCamara() {

    if (flujoCamara) {

        flujoCamara
            .getTracks()
            .forEach(
                track => track.stop()
            );

        flujoCamara = null;

    }


    const video =
        document.getElementById(
            "videoCamara"
        );


    video.srcObject = null;

    video.style.display = "none";


    document.getElementById(
        "estadoCamara"
    ).innerText =
        "📷 Cámara apagada";

}


// ============================================================
// CAMBIAR CÁMARA
// ============================================================

async function cambiarCamara() {

    camaraActual =
        camaraActual === "environment"
            ? "user"
            : "environment";


    if (flujoCamara) {

        await activarCamara();

    }

}


// ============================================================
// CREAR PEER CONNECTION
// ============================================================

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
                        candidate: event.candidate
                    }
                );

            }

        };


    peerConnection.ontrack =
        function(event) {

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
                    .catch(
                        error =>
                            console.log(
                                "Autoplay:",
                                error
                            )
                    );


                document.getElementById(
                    "estadoTransmision"
                ).innerText =
                    "🟢 Cámara del teléfono conectada";

            }

        };


    peerConnection.onconnectionstatechange =
        function() {

            if (
                peerConnection.connectionState ===
                "connected"
            ) {

                document.getElementById(
                    "estadoTransmision"
                ).innerText =
                    "🟢 Cámara conectada";

            }


            if (
                peerConnection.connectionState ===
                "failed"
            ) {

                document.getElementById(
                    "estadoTransmision"
                ).innerText =
                    "❌ No se pudo establecer la conexión";

            }


            if (
                peerConnection.connectionState ===
                "disconnected"
            ) {

                document.getElementById(
                    "estadoTransmision"
                ).innerText =
                    "🟡 Cámara desconectada";

            }

        };


    return peerConnection;

}


// ============================================================
// INICIAR TRANSMISIÓN
// ============================================================

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
            resultado.estado !==
            "ok"
        ) {

            alert(
                "No se pudo crear la cámara."
            );

            return;

        }


        salaActual =
            resultado.codigo;


        soyTransmisor = true;

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


    } catch (error) {

        console.error(
            "Error iniciando transmisión:",
            error
        );


        alert(
            "No se pudo iniciar la transmisión."
        );

    }

}


// ============================================================
// VER CÁMARA
// ============================================================

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

        soyTransmisor = false;

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


    } catch (error) {

        console.error(
            "Error conectando:",
            error
        );


        alert(
            "No se pudo conectar con la cámara."
        );

    }

}


// ============================================================
// USUARIO UNIDO
// ============================================================

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
                    track =>
                        peerConnection.addTrack(
                            track,
                            flujoCamara
                        )
                );


            const oferta =
                await peerConnection.createOffer();


            await peerConnection.setLocalDescription(
                oferta
            );


            socket.emit(
                "oferta",
                {
                    sala: salaActual,
                    oferta:
                        peerConnection.localDescription
                }
            );


            document.getElementById(
                "estadoTransmision"
            ).innerText =
                "🟡 Conectando con la computadora...";


        } catch (error) {

            console.error(
                "Error creando oferta:",
                error
            );

        }

    }
);


// ============================================================
// OFERTA
// ============================================================

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


            await peerConnection.setRemoteDescription(
                new RTCSessionDescription(
                    data.oferta
                )
            );


            while (
                candidatosPendientes.length > 0
            ) {

                const candidato =
                    candidatosPendientes.shift();


                await peerConnection.addIceCandidate(
                    candidato
                );

            }


            const respuesta =
                await peerConnection.createAnswer();


            await peerConnection.setLocalDescription(
                respuesta
            );


            socket.emit(
                "respuesta",
                {
                    sala: data.sala,
                    respuesta:
                        peerConnection.localDescription
                }
            );


        } catch (error) {

            console.error(
                "Error procesando oferta:",
                error
            );

        }

    }
);


// ============================================================
// RESPUESTA
// ============================================================

socket.on(
    "respuesta",
    async function(data) {

        if (!soyTransmisor) {
            return;
        }


        try {

            await peerConnection.setRemoteDescription(
                new RTCSessionDescription(
                    data.respuesta
                )
            );


            while (
                candidatosPendientes.length > 0
            ) {

                const candidato =
                    candidatosPendientes.shift();


                await peerConnection.addIceCandidate(
                    candidato
                );

            }

        } catch (error) {

            console.error(
                "Error procesando respuesta:",
                error
            );

        }

    }
);


// ============================================================
// CANDIDATOS ICE
// ============================================================

socket.on(
    "candidato",
    async function(data) {

        try {

            if (
                !peerConnection ||
                !data.candidate
            ) {
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


            await peerConnection.addIceCandidate(
                candidato
            );


        } catch (error) {

            console.error(
                "Error ICE:",
                error
            );

        }

    }
);


// ============================================================
// ERROR DE CÁMARA
// ============================================================

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


// ============================================================
// DETENER VIDEO REMOTO
// ============================================================

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

    video.style.display = "none";


    candidatosPendientes = [];

    salaActual = null;


    document.getElementById(
        "estadoTransmision"
    ).innerText =
        "📡 Cámara sin conexión";

}


// ============================================================
// ANALIZAR CULTIVO
// ============================================================

async function analizarCultivo() {

    const video =
        document.getElementById(
            "videoRemoto"
        );


    const resultado =
        document.getElementById(
            "resultadoAnalisis"
        );


    if (
        !video.srcObject ||
        video.readyState < 2 ||
        video.videoWidth === 0
    ) {

        resultado.innerText =
            "❌ Primero conecta la cámara del teléfono.";

        return;

    }


    try {

        resultado.innerText =
            "🔍 Analizando cultivo...";


        const canvas =
            document.createElement(
                "canvas"
            );


        canvas.width =
            video.videoWidth;


        canvas.height =
            video.videoHeight;


        const contexto =
            canvas.getContext(
                "2d"
            );


        contexto.drawImage(
            video,
            0,
            0,
            canvas.width,
            canvas.height
        );


        const imagen =
            canvas.toDataURL(
                "image/jpeg",
                0.8
            );


        const respuesta =
            await fetch(
                "/api/camara/analizar",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        imagen: imagen
                    })
                }
            );


        const resultadoServidor =
            await respuesta.json();


        resultado.innerText =
            resultadoServidor.mensaje;


        document.getElementById(
            "alerta"
        ).innerText =
            resultadoServidor.mensaje;


    } catch (error) {

        console.error(
            "Error analizando:",
            error
        );


        resultado.innerText =
            "❌ Error durante el análisis.";

    }

}


// ============================================================
// ACTUALIZAR DATOS
// ============================================================

async function actualizarDatos() {

    try {

        const respuesta =
            await fetch(
                "/api/datos"
            );


        const datosServidor =
            await respuesta.json();


        document.getElementById(
            "temperatura"
        ).innerText =
            Number(
                datosServidor.temperatura
            ).toFixed(1) +
            " °C";


        document.getElementById(
            "humedad"
        ).innerText =
            Number(
                datosServidor.humedad
            ).toFixed(1) +
            " %";


        document.getElementById(
            "suelo"
        ).innerText =
            datosServidor.suelo +
            " %";


        const bomba =
            document.getElementById(
                "riego"
            );


        if (datosServidor.riego) {

            bomba.innerText =
                "ENCENDIDA";

            bomba.className =
                "valor verde";

        } else {

            bomba.innerText =
                "APAGADA";

            bomba.className =
                "valor rojo";

        }


        let textoEstado;


        if (
            datosServidor.modo ===
            "automatico"
        ) {

            textoEstado =
                "🤖 Modo automático";

        } else {

            textoEstado =
                "👨‍🌾 Modo manual";

        }


        if (
            datosServidor.automatico_pausado
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
            datosServidor.alerta;


    } catch (error) {

        console.log(
            "Error obteniendo datos:",
            error
        );

    }

}


// ============================================================
// CAMBIAR MODO
// ============================================================

async function cambiarModo(modo) {

    try {

        const respuesta =
            await fetch(
                "/api/riego",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        accion: "modo",
                        modo: modo
                    })
                }
            );


        const resultado =
            await respuesta.json();


        alert(
            resultado.mensaje
        );


        actualizarDatos();


    } catch (error) {

        alert(
            "Error de comunicación"
        );

    }

}


// ============================================================
// CONTROLAR RIEGO
// ============================================================

async function controlarRiego(accion) {

    try {

        const respuesta =
            await fetch(
                "/api/riego",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        accion: accion
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


        actualizarDatos();


    } catch (error) {

        alert(
            "Error de comunicación"
        );

    }

}


// ============================================================
// REACTIVAR AUTOMÁTICO
// ============================================================

async function reactivarAutomatico() {

    try {

        const respuesta =
            await fetch(
                "/api/riego",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        accion: "reactivar"
                    })
                }
            );


        const resultado =
            await respuesta.json();


        alert(
            resultado.mensaje
        );


        actualizarDatos();


    } catch (error) {

        alert(
            "Error de comunicación"
        );

    }

}


// ============================================================
// INICIO
// ============================================================

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
# RUTA PRINCIPAL
# ============================================================

@app.route("/")
def index():
    return render_template_string(HTML)


# ============================================================
# DATOS
# ============================================================

@app.route(
    "/api/datos",
    methods=["GET"]
)
def obtener_datos():

    return jsonify(datos)


# ============================================================
# CONTROL DE RIEGO
# ============================================================

@app.route(
    "/api/riego",
    methods=["POST"]
)
def gestionar_riego():

    peticion = request.get_json() or {}

    accion = peticion.get("accion")


    if accion == "modo":

        nuevo_modo =
            peticion.get(
                "modo",
                "automatico"
            )


        if nuevo_modo not in [
            "automatico",
            "manual"
        ]:

            return jsonify({
                "estado": "error",
                "mensaje": "Modo no válido"
            }), 400


        datos["modo"] =
            nuevo_modo


        orden_riego["modo"] =
            nuevo_modo


        if nuevo_modo == "automatico":

            datos["automatico_pausado"] =
                False

            orden_riego[
                "automatico_pausado"
            ] = False

            mensaje =
                "Modo automático activado."

        else:

            mensaje =
                "Modo manual activado."


        datos["alerta"] =
            mensaje


        return jsonify({
            "estado": "ok",
            "mensaje": mensaje
        })


    elif accion == "encender":

        datos["riego"] =
            True


        orden_riego["riego"] =
            True


        if datos["modo"] == "automatico":

            datos[
                "automatico_pausado"
            ] = True

            orden_riego[
                "automatico_pausado"
            ] = True


            mensaje =
                "Riego activado manualmente. Control automático pausado."

        else:

            mensaje =
                "Riego encendido en modo manual."


        datos["alerta"] =
            mensaje


        return jsonify({
            "estado": "ok",
            "mensaje": mensaje
        })


    elif accion == "apagar":

        datos["riego"] =
            False


        orden_riego["riego"] =
            False


        if datos["modo"] == "automatico":

            datos[
                "automatico_pausado"
            ] = True

            orden_riego[
                "automatico_pausado"
            ] = True


            mensaje =
                "Riego detenido manualmente. Control automático pausado."

        else:

            mensaje =
                "Riego apagado en modo manual."


        datos["alerta"] =
            mensaje


        return jsonify({
            "estado": "ok",
            "mensaje": mensaje
        })


    elif accion == "reactivar":

        datos["modo"] =
            "automatico"


        datos[
            "automatico_pausado"
        ] = False


        orden_riego["modo"] =
            "automatico"


        orden_riego[
            "automatico_pausado"
        ] = False


        datos["riego"] =
            False


        orden_riego["riego"] =
            False


        mensaje =
            "Control automático reactivado."


        datos["alerta"] =
            mensaje


        return jsonify({
            "estado": "ok",
            "mensaje": mensaje
        })


    return jsonify({
        "estado": "error",
        "mensaje": "Acción no válida"
    }), 400


# ============================================================
# DATOS DESDE ESP32
# ============================================================

@app.route(
    "/api/actualizar",
    methods=["POST"]
)
def actualizar_desde_esp32():

    peticion =
        request.get_json() or {}


    if "temperatura" in peticion:

        datos["temperatura"] =
            float(
                peticion["temperatura"]
            )


    if "humedad" in peticion:

        datos["humedad"] =
            float(
                peticion["humedad"]
            )


    if "suelo" in peticion:

        datos["suelo"] =
            int(
                peticion["suelo"]
            )


    # --------------------------------------------------------
    # RIEGO AUTOMÁTICO
    # --------------------------------------------------------

    if (
        datos["modo"] == "automatico"
        and not datos["automatico_pausado"]
    ):

        if datos["suelo"] < 30:

            datos["riego"] =
                True

            orden_riego["riego"] =
                True

            datos["alerta"] =
                "Humedad baja detectada. Riego encendido automáticamente."


        elif datos["suelo"] > 70:

            datos["riego"] =
                False

            orden_riego["riego"] =
                False

            datos["alerta"] =
                "Humedad adecuada. Riego apagado."


    return jsonify({
        "estado": "ok",
        "orden": orden_riego
    })


# ============================================================
# CREAR SALA DE CÁMARA
# ============================================================

@app.route(
    "/api/camara/nueva",
    methods=["POST"]
)
def crear_sala_camara():

    codigo =
        generar_codigo()


    salas_camara[codigo] = {
        "activa": True
    }


    return jsonify({
        "estado": "ok",
        "codigo": codigo
    })


# ============================================================
# ANALIZAR IMAGEN DE CÁMARA
# ============================================================

@app.route(
    "/api/camara/analizar",
    methods=["POST"]
)
def analizar_imagen_camara():

    global imagen_anterior


    peticion =
        request.get_json() or {}


    imagen_b64 =
        peticion.get(
            "imagen",
            ""
        )


    if not imagen_b64:

        return jsonify({
            "estado": "error",
            "mensaje":
                "No se recibió ninguna imagen."
        }), 400


    try:

        # ----------------------------------------------------
        # DECODIFICAR IMAGEN
        # ----------------------------------------------------

        if "," in imagen_b64:

            imagen_b64 =
                imagen_b64.split(
                    ",",
                    1
                )[1]


        datos_imagen =
            base64.b64decode(
                imagen_b64
            )


        imagen_actual =
            Image.open(
                io.BytesIO(
                    datos_imagen
                )
            ).convert("RGB")


        # ----------------------------------------------------
        # REDUCIR IMAGEN
        # ----------------------------------------------------

        imagen_actual =
            imagen_actual.resize(
                (160, 120)
            )


        # ----------------------------------------------------
        # PRIMERA IMAGEN
        # ----------------------------------------------------

        if imagen_anterior is None:

            imagen_anterior =
                imagen_actual.copy()


            mensaje =
                "📸 Imagen base guardada. Realiza otro análisis para comparar."


            datos["alerta"] =
                mensaje


            return jsonify({
                "estado": "ok",
                "alerta": False,
                "mensaje": mensaje
            })


        # ----------------------------------------------------
        # COMPARAR IMÁGENES
        # ----------------------------------------------------

        diferencia =
            ImageChops.difference(
                imagen_actual,
                imagen_anterior
            )


        estadisticas =
            ImageStat.Stat(
                diferencia
            )


        promedio_cambio =
            sum(
                estadisticas.mean
            ) / len(
                estadisticas.mean
            )


        # Guardar imagen actual
        # para la siguiente comparación

        imagen_anterior =
            imagen_actual.copy()


        # ----------------------------------------------------
        # DETECCIÓN
        # ----------------------------------------------------

        if promedio_cambio > 25:

            mensaje =
                "🚨 POSIBLE ANOMALÍA DETECTADA"


            datos["alerta"] =
                mensaje


            return jsonify({
                "estado": "ok",
                "alerta": True,
                "mensaje": mensaje
            })


        mensaje =
            "🟢 Cultivo estable. Sin anomalías visibles."


        datos["alerta"] =
            mensaje


        return jsonify({
            "estado": "ok",
            "alerta": False,
            "mensaje": mensaje
        })


    except Exception as error:

        print(
            "Error procesando imagen:",
            error
        )


        return jsonify({
            "estado": "error",
            "mensaje":
                "❌ Error procesando la imagen."
        }), 500


# ============================================================
# SOCKET.IO - CREAR SALA
# ============================================================

@socketio.on("crear_sala")
def al_crear_sala(data):

    sala =
        data.get(
            "sala"
        )


    if sala:

        join_room(
            sala
        )


# ============================================================
# SOCKET.IO - UNIRSE
# ============================================================

@socketio.on("unirse_sala")
def al_unirse_sala(data):

    sala =
        data.get(
            "sala"
        )


    if sala in salas_camara:

        join_room(
            sala
        )


        emit(
            "usuario_unido",
            to=sala
        )


    else:

        emit(
            "error_camara",
            {
                "mensaje":
                    "Código de cámara inválido o expirado."
            }
        )


# ============================================================
# SOCKET.IO - OFERTA
# ============================================================

@socketio.on("oferta")
def al_recibir_oferta(data):

    sala =
        data.get(
            "sala"
        )


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
def al_recibir_respuesta(data):

    sala =
        data.get(
            "sala"
        )


    if sala:

        emit(
            "respuesta",
            data,
            to=sala,
            include_self=False
        )


# ============================================================
# SOCKET.IO - CANDIDATO
# ============================================================

@socketio.on("candidato")
def al_recibir_candidato(data):

    sala =
        data.get(
            "sala"
        )


    if sala:

        emit(
            "candidato",
            data,
            to=sala,
            include_self=False
        )


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False
    )
