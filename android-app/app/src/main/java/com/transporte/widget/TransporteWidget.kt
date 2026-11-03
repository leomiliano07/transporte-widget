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
        private const val ACTION_REFRESH = "com.transporte.widget.REFRESH"
        private const val JSON_URL = "https://raw.githubusercontent.com/leomiliano07/transporte-widget/main/status.json"
    }

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        for (id in appWidgetIds) {
            setupClick(context, id, appWidgetManager)
            actualizar(context, appWidgetManager, id)
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == ACTION_REFRESH) {
            val manager = AppWidgetManager.getInstance(context)
            val ids = manager.getAppWidgetIds(ComponentName(context, TransporteWidget::class.java))
            for (id in ids) {
                actualizar(context, manager, id)
            }
        }
    }

    private fun setupClick(context: Context, widgetId: Int, manager: AppWidgetManager) {
        val views = RemoteViews(context.packageName, R.layout.widget_layout)
        val intent = Intent(context, TransporteWidget::class.java).apply {
            action = ACTION_REFRESH
        }
        val pendingIntent = PendingIntent.getBroadcast(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_root, pendingIntent)
        manager.updateAppWidget(widgetId, views)
    }

    private fun actualizar(context: Context, manager: AppWidgetManager, widgetId: Int) {
        val views = RemoteViews(context.packageName, R.layout.widget_layout)
        views.setTextViewText(R.id.txt_hora, "Cargando...")
        manager.updateAppWidget(widgetId, views)

        thread {
            try {
                val url = URL(JSON_URL)
                val conn = url.openConnection() as HttpURLConnection
                conn.connectTimeout = 6000
                conn.readTimeout = 6000
                conn.useCaches = false

                val text = conn.inputStream.bufferedReader().use { it.readText() }
                val json = JSONObject(text)

                val subte = json.getJSONObject("subte_c").getString("estado")
                val roca = json.getJSONObject("tren_roca").getString("estado")
                val hora = json.getString("actualizado")

                views.setTextViewText(R.id.txt_subte, "Subte C: $subte")
                views.setTextViewText(R.id.txt_roca, "Roca Korn: $roca")
                views.setTextViewText(R.id.txt_hora, "Actualizado: $hora hs")
            } catch (e: Exception) {
                views.setTextViewText(R.id.txt_hora, "Error al conectar (toca aquí)")
            }
            manager.updateAppWidget(widgetId, views)
        }
    }
}
