package com.transporte.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

class TransporteWidget : AppWidgetProvider() {

    companion object {
        const val ACTION_REFRESH = "com.transporte.widget.ACTION_REFRESH"
        private const val JSON_URL = "https://raw.githubusercontent.com/leomiliano07/transporte-widget/main/status.json"
    }

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        for (id in appWidgetIds) {
            actualizar(context, appWidgetManager, id)
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == ACTION_REFRESH || intent.action == AppWidgetManager.ACTION_APPWIDGET_UPDATE) {
            val manager = AppWidgetManager.getInstance(context)
            val ids = manager.getAppWidgetIds(ComponentName(context, TransporteWidget::class.java))
            for (id in ids) {
                actualizar(context, manager, id)
            }
        }
    }

    private fun getClickPendingIntent(context: Context): PendingIntent {
        val intent = Intent(context, TransporteWidget::class.java).apply {
            action = ACTION_REFRESH
        }
        return PendingIntent.getBroadcast(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private fun actualizar(context: Context, manager: AppWidgetManager, widgetId: Int) {
        val pendingIntent = getClickPendingIntent(context)

        // Estado inicial de carga
        val views = RemoteViews(context.packageName, R.layout.widget_layout).apply {
            setTextViewText(R.id.txt_hora, "Cargando...")
            setOnClickPendingIntent(R.id.widget_root, pendingIntent)
            setOnClickPendingIntent(R.id.txt_titulo, pendingIntent)
            setOnClickPendingIntent(R.id.txt_hora, pendingIntent)
        }
        manager.updateAppWidget(widgetId, views)

        thread {
            try {
                val url = URL(JSON_URL)
                val conn = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "GET"
                    setRequestProperty("User-Agent", "Mozilla/5.0")
                    connectTimeout = 8000
                    readTimeout = 8000
                    useCaches = false
                }

                val text = conn.inputStream.bufferedReader().use { it.readText() }
                val json = JSONObject(text)

                val subte = json.optJSONObject("subte_c")?.optString("estado", "Normal") ?: "Normal"
                val subteMsg = json.optJSONObject("subte_c")?.optString("mensaje", "") ?: ""
                val roca = json.optJSONObject("tren_roca")?.optString("estado", "Normal") ?: "Normal"
                val rocaMsg = json.optJSONObject("tren_roca")?.optString("mensaje", "") ?: ""
                val hora = json.optString("actualizado", "--:--")

                val updatedViews = RemoteViews(context.packageName, R.layout.widget_layout).apply {
                    setTextViewText(R.id.txt_subte, "Subte C: $subte")
                    setTextViewText(R.id.txt_roca, "Roca Korn: $roca")
                    setTextViewText(R.id.txt_hora, "Act: $hora hs (toca para refrescar)")
                    setOnClickPendingIntent(R.id.widget_root, pendingIntent)
                    setOnClickPendingIntent(R.id.txt_titulo, pendingIntent)
                    setOnClickPendingIntent(R.id.txt_hora, pendingIntent)
                }
                manager.updateAppWidget(widgetId, updatedViews)

            } catch (e: Exception) {
                val errViews = RemoteViews(context.packageName, R.layout.widget_layout).apply {
                    setTextViewText(R.id.txt_hora, "Error conexión. Toca para reintentar")
                    setOnClickPendingIntent(R.id.widget_root, pendingIntent)
                    setOnClickPendingIntent(R.id.txt_titulo, pendingIntent)
                    setOnClickPendingIntent(R.id.txt_hora, pendingIntent)
                }
                manager.updateAppWidget(widgetId, errViews)
            }
        }
    }
}
