from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# ============================================================
# DATOS DEL SISTEMA
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
    "riego": False,
    "automatico_pausado": False
}

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
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

button:hover {
    opacity: 0.85;
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

.amarillo {
    color: #ffca28;
}

.azul {
    color: #42a5f5;
}

.info {
    text-align: center;
    color: #bdbdbd;
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


<!-- =====================================================
     DATOS
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
     CONTROL
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


<div class="estado" id="estado">

Cargando estado...

</div>

</div>


<div class="tarjeta">

<h2>📢 Estado del sistema</h2>

<div class="estado" id="alerta">

Esperando información...

</div>

<p class="info">

Los datos se actualizan automáticamente.

</p>

</div>


</div>


<script>

// ========================================================
// OBTENER DATOS
// ========================================================

async function actualizarDatos() {

    try {

        const respuesta =
            await fetch("/api/datos");

        const datos =
            await respuesta.json();


        document.getElementById(
            "temperatura"
        ).innerText =
            Number(datos.temperatura).toFixed(1)
            + " °C";


        document.getElementById(
            "humedad"
        ).innerText =
            Number(datos.humedad).toFixed(1)
            + " %";


        document.getElementById(
            "suelo"
        ).innerText =
            datos.suelo + " %";


        const bomba =
            document.getElementById("riego");


        if (datos.riego) {

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


        let textoEstado =
            "Modo: " + datos.modo;


        if (datos.modo === "automatico") {

            textoEstado =
                "🤖 Modo automático";

        } else {

            textoEstado =
                "👨‍🌾 Modo manual";
        }


        if (datos.automatico_pausado) {

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


    } catch(error) {

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


        alert(resultado.mensaje);

        actualizarDatos();


    } catch(error) {

        alert(
            "Error de comunicación"
        );

    }

}


// ========================================================
// REGAR / DETENER
// ========================================================

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


        if (resultado.estado === "error") {

            alert(
                resultado.mensaje
            );

        } else {

            actualizarDatos();
        }


    } catch(error) {

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
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        accion:
                            "reactivar"
                    })
                }
            );


        const resultado =
            await respuesta.json();


        alert(resultado.mensaje);

        actualizarDatos();


    } catch(error) {

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

    return render_template_string(HTML)


# ============================================================
# API DATOS - GET
# ============================================================

@app.route("/api/datos", methods=["GET"])
def obtener_datos():

    datos["automatico_pausado"] = \
        orden_riego["automatico_pausado"]

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

        if not solicitud:

            return jsonify({
                "estado": "error",
                "mensaje": "No se recibieron datos"
            }), 400

        accion = solicitud.get("accion")


        # ====================================================
        # CAMBIAR MODO
        # ====================================================

        if accion == "modo":

            modo = solicitud.get("modo")


            if modo not in [
                "automatico",
                "manual"
            ]:

                return jsonify({
                    "estado": "error",
                    "mensaje": "Modo no válido"
                }), 400


            orden_riego["modo"] = modo

            datos["modo"] = modo

            # Al cambiar de modo se reinicia la pausa
            orden_riego["automatico_pausado"] = False

            # Apagar bomba al cambiar de modo
            orden_riego["riego"] = False

            datos["riego"] = False


            if modo == "automatico":

                datos["alerta"] = \
                    "🤖 Riego automático activado"

            else:

                datos["alerta"] = \
                    "👨‍🌾 Riego manual activado"


            return jsonify({
                "estado": "ok",
                "mensaje": datos["alerta"]
            })


        # ====================================================
        # ENCENDER / REGAR
        # ====================================================

        if accion == "encender":

            # En cualquier modo se puede forzar el riego
            orden_riego["riego"] = True

            datos["riego"] = True

            datos["alerta"] = \
                "💧 Riego activado"


            return jsonify({
                "estado": "ok",
                "mensaje": "💧 Riego activado"
            })


        # ====================================================
        # DETENER
        # ====================================================

        if accion == "apagar":

            orden_riego["riego"] = False

            datos["riego"] = False

            # Si estaba en automático,
            # lo dejamos pausado.

            if orden_riego["modo"] == "automatico":

                orden_riego[
                    "automatico_pausado"
                ] = True

                datos["alerta"] = \
                    "🛑 Riego detenido. Automático pausado"

            else:

                datos["alerta"] = \
                    "🛑 Riego detenido"


            return jsonify({
                "estado": "ok",
                "mensaje": datos["alerta"]
            })


        # ====================================================
        # REACTIVAR AUTOMÁTICO
        # ====================================================

        if accion == "reactivar":

            orden_riego["modo"] = \
                "automatico"

            datos["modo"] = \
                "automatico"

            orden_riego[
                "automatico_pausado"
            ] = False

            orden_riego["riego"] = False

            datos["riego"] = False

            datos["alerta"] = \
                "▶️ Riego automático reactivado"


            return jsonify({
                "estado": "ok",
                "mensaje":
                    "▶️ Riego automático reactivado"
            })


        # ====================================================
        # ACCIÓN NO VÁLIDA
        # ====================================================

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

                datos["temperatura"] = \
                    nuevos_datos["temperatura"]


            if "humedad" in nuevos_datos:

                datos["humedad"] = \
                    nuevos_datos["humedad"]


            if "suelo" in nuevos_datos:

                datos["suelo"] = \
                    nuevos_datos["suelo"]


            if "riego" in nuevos_datos:

                datos["riego"] = \
                    nuevos_datos["riego"]


            if "modo" in nuevos_datos:

                datos["modo"] = \
                    nuevos_datos["modo"]


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
# SERVIDOR
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
