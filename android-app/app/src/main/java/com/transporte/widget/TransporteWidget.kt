package com.transporte.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.security.SecureRandom
import java.security.cert.X509Certificate
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import javax.net.ssl.HostnameVerifier
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManager
import javax.net.ssl.X509TrustManager
import kotlin.concurrent.thread

class TransporteWidget : AppWidgetProvider() {

    companion object {
        const val ACTION_REFRESH = "com.transporte.widget.ACTION_REFRESH"
    }

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        // Todo el trabajo se traslada a onReceive para poder usar goAsync()
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        
        if (intent.action == ACTION_REFRESH || intent.action == AppWidgetManager.ACTION_APPWIDGET_UPDATE) {
            
            val manager = AppWidgetManager.getInstance(context)
            val ids = manager.getAppWidgetIds(ComponentName(context, TransporteWidget::class.java))
            
            // Le avisa a Android que haremos trabajo en segundo plano para que NO mate la app
            val pendingResult = goAsync() 

            for (id in ids) {
                val loadingViews = RemoteViews(context.packageName, R.layout.widget_layout).apply {
                    setTextViewText(R.id.txt_hora, "Actualizando...")
                    vincularClicks(this, getClickPendingIntent(context))
                }
                manager.updateAppWidget(id, loadingViews)
            }

            // Ejecutar la red en hilo secundario protegido
            thread {
                try {
                    for (id in ids) {
                        realizarConsultaRed(context, manager, id)
                    }
                } finally {
                    // Libera el proceso una vez que los datos se actualizaron en pantalla
                    pendingResult.finish()
                }
            }
        }
    }

    private fun getClickPendingIntent(context: Context): PendingIntent {
        val intent = Intent(context, TransporteWidget::class.java).apply {
            action = ACTION_REFRESH
        }
        return PendingIntent.getBroadcast(
            context, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private fun vincularClicks(views: RemoteViews, pendingIntent: PendingIntent) {
        views.setOnClickPendingIntent(R.id.widget_root, pendingIntent)
        views.setOnClickPendingIntent(R.id.txt_titulo, pendingIntent)
        views.setOnClickPendingIntent(R.id.txt_subte, pendingIntent)
        views.setOnClickPendingIntent(R.id.txt_roca, pendingIntent)
        views.setOnClickPendingIntent(R.id.txt_hora, pendingIntent)
    }

    private fun descargarJson(urlStr: String): String {
        val trustAllCerts = arrayOf<TrustManager>(object : X509TrustManager {
            override fun getAcceptedIssuers(): Array<X509Certificate> = arrayOf()
            override fun checkClientTrusted(certs: Array<X509Certificate>, authType: String) {}
            override fun checkServerTrusted(certs: Array<X509Certificate>, authType: String) {}
        })

        val sslContext = SSLContext.getInstance("TLS").apply {
            init(null, trustAllCerts, SecureRandom())
        }

        val url = URL("$urlStr?t=${System.currentTimeMillis()}")
        val conn = (url.openConnection() as HttpURLConnection).apply {
            if (this is HttpsURLConnection) {
                sslSocketFactory = sslContext.socketFactory
                hostnameVerifier = HostnameVerifier { _, _ -> true }
            }
            requestMethod = "GET"
            setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            setRequestProperty("Cache-Control", "no-cache")
            connectTimeout = 9000
            readTimeout = 9000
            useCaches = false
        }
        return conn.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
    }

    private fun formatearIcono(estadoRaw: String, mensajeRaw: String): String {
        val estado = estadoRaw.trim()
        val mensaje = mensajeRaw.trim()
        val textoCompleto = "$estado $mensaje".lowercase()

        return when {
            textoCompleto.contains("interrumpido") || textoCompleto.contains("suspendido") ||
            textoCompleto.contains("cancelado") || textoCompleto.contains("cerrad") -> {
                val detalle = if (mensaje.isNotEmpty()) mensaje else estado
                "❌ $detalle"
            }
            textoCompleto.contains("demora") || textoCompleto.contains("limitado") ||
            textoCompleto.contains("reducido") || textoCompleto.contains("alerta") -> {
                val detalle = if (mensaje.isNotEmpty()) mensaje else estado
                "⚠️ $detalle"
            }
            else -> "✅"
        }
    }

    private fun getSubteC(): String {
        try {
            val raw = descargarJson("https://www.metrovias.com.ar/servicios/subte.json")
            val data = JSONArray(raw)
            for (i in 0 until data.length()) {
                val linea = data.getJSONObject(i)
                if (linea.optString("linea", "") == "C" || linea.optString("nombre", "").contains("C", true)) {
                    return formatearIcono(linea.optString("estado", "Normal"), linea.optString("mensaje", ""))
                }
            }
        } catch (e: Exception) { }
        return "✅"
    }

    private fun getTrenRocaKorn(): String {
        try {
            val raw = descargarJson("https://trenesargentinos.gob.ar/api/estado-lineas")
            val data = JSONObject(raw)
            val lineas = data.optJSONArray("lineas") ?: JSONArray()
            for (i in 0 until lineas.length()) {
                val linea = lineas.getJSONObject(i)
                if (linea.optString("nombre", "").lowercase().contains("roca")) {
                    val ramales = linea.optJSONArray("ramales") ?: JSONArray()
                    for (j in 0 until ramales.length()) {
                        val ramal = ramales.getJSONObject(j)
                        if (ramal.optString("nombre", "").lowercase().contains("korn")) {
                            return formatearIcono(ramal.optString("estado", "Normal"), ramal.optString("mensaje", ""))
                        }
                    }
                }
            }
        } catch (e: Exception) { }
        return "✅"
    }

    private fun realizarConsultaRed(context: Context, manager: AppWidgetManager, widgetId: Int) {
        val subte = getSubteC()
        val roca = getTrenRocaKorn()

        val sdf = SimpleDateFormat("HH:mm", Locale.getDefault()).apply {
            timeZone = TimeZone.getTimeZone("America/Argentina/Buenos_Aires")
        }
        val now = sdf.format(Date())

        val updatedViews = RemoteViews(context.packageName, R.layout.widget_layout).apply {
            setTextViewText(R.id.txt_subte, "Subte C: $subte")
            setTextViewText(R.id.txt_roca, "Roca Korn: $roca")
            setTextViewText(R.id.txt_hora, "Act: $now hs")
            vincularClicks(this, getClickPendingIntent(context))
        }
        manager.updateAppWidget(widgetId, updatedViews)
    }
}
