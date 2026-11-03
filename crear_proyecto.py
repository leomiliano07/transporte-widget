import os

# ==========================================
# CONFIGURA TUS DATOS DE GITHUB AQUÍ
# ==========================================
GITHUB_USER = "leomiliano07"
GITHUB_REPO = "transporte-widget"
# ==========================================

ARCHIVOS = {
    # 1. GitHub Workflows
    ".github/workflows/actualizar_datos.yml": """name: Actualizar Estado

on:
  schedule:
    - cron: '*/15 8-23 * * 1-5'
    - cron: '*/15 0-2 * * 2-6'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  run-scraper:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instalar pytz
        run: pip install pytz

      - name: Ejecutar script
        run: python backend/fetch_status.py

      - name: Guardar cambios
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add status.json
          git commit -m "chore: status.json actualizado [skip ci]" || exit 0
          git push
""",

    ".github/workflows/compilar_apk.yml": """name: Compilar APK

on:
  workflow_dispatch:
  push:
    paths:
      - 'android-app/**'
      - '.github/workflows/compilar_apk.yml'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Java 17
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3

      - name: Generar Wrapper si falta y dar permisos
        run: |
          cd android-app
          gradle wrapper
          chmod +x gradlew

      - name: Compilar APK Debug
        run: |
          cd android-app
          ./gradlew assembleDebug --no-daemon

      - name: Subir APK
        uses: actions/upload-artifact@v4
        with:
          name: TransporteWidget-APK
          path: android-app/app/build/outputs/apk/debug/*.apk
""",

    # 2. Backend
    "backend/fetch_status.py": """import json
import urllib.request
from datetime import datetime
import pytz

def get_subte_c():
    url = "https://www.metrovias.com.ar/servicios/subte.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode())
            for linea in data:
                if linea.get("linea") == "C" or "Línea C" in linea.get("nombre", ""):
                    return {
                        "estado": linea.get("estado", "Normal"),
                        "mensaje": linea.get("mensaje", "").strip() or "Servicio normal"
                    }
    except Exception:
        pass
    return {"estado": "Normal", "mensaje": "Sin novedades"}

def get_tren_roca_korn():
    url = "https://trenesargentinos.gob.ar/api/estado-lineas"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode())
            for linea in data.get("lineas", []):
                if "roca" in linea.get("nombre", "").lower():
                    for ramal in linea.get("ramales", []):
                        if "korn" in ramal.get("nombre", "").lower():
                            return {
                                "estado": ramal.get("estado", "Normal"),
                                "mensaje": ramal.get("mensaje", "").strip() or "A horario"
                            }
    except Exception:
        pass
    return {"estado": "Normal", "mensaje": "A horario"}

def main():
    tz = pytz.timezone('America/Argentina/Buenos_Aires')
    now = datetime.now(tz).strftime("%H:%M")

    payload = {
        "actualizado": now,
        "subte_c": get_subte_c(),
        "tren_roca": get_tren_roca_korn()
    }

    with open("status.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
""",

    # 3. Android App: Configuración y Gradle
    "android-app/settings.gradle": """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "TransporteWidgetApp"
include ':app'
""",

    "android-app/build.gradle": """plugins {
    id 'com.android.application' version '8.2.2' apply false
    id 'org.jetbrains.kotlin.android' version '1.9.22' apply false
}
""",

    "android-app/app/build.gradle": """plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}

android {
    namespace 'com.transporte.widget'
    compileSdk 34

    defaultConfig {
        applicationId "com.transporte.widget"
        minSdk 26
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
        }
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = '17'
    }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.12.0'
}
""",

    "android-app/gradle/wrapper/gradle-wrapper.properties": """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.2-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""",

    # 4. Android App: Recursos y Manifest
    "android-app/app/src/main/AndroidManifest.xml": """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="true"
        android:icon="@android:drawable/sym_def_app_icon"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar">

        <receiver
            android:name=".TransporteWidget"
            android:exported="true">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/widget_info" />
        </receiver>

    </application>
</manifest>
""",

    "android-app/app/src/main/res/values/strings.xml": """<resources>
    <string name="app_name">Estado Transporte</string>
</resources>
""",

    "android-app/app/src/main/res/xml/widget_info.xml": """<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="180dp"
    android:minHeight="110dp"
    android:updatePeriodMillis="1800000"
    android:initialLayout="@layout/widget_layout"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen" />
""",

    "android-app/app/src/main/res/layout/widget_layout.xml": """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/widget_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="12dp"
    android:background="#E61E1E1E">

    <TextView
        android:id="@+id/txt_titulo"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Estado Transporte ⟳"
        android:textColor="#9E9E9E"
        android:textSize="11sp" />

    <TextView
        android:id="@+id/txt_subte"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_marginTop="6dp"
        android:text="Subte C: ..."
        android:textColor="#FFFFFF"
        android:textSize="13sp"
        android:textStyle="bold" />

    <TextView
        android:id="@+id/txt_roca"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_marginTop="4dp"
        android:text="Roca Korn: ..."
        android:textColor="#FFFFFF"
        android:textSize="13sp"
        android:textStyle="bold" />

    <TextView
        android:id="@+id/txt_hora"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_marginTop="6dp"
        android:text="Toca para actualizar"
        android:textColor="#757575"
        android:textSize="10sp" />
</LinearLayout>
""",

    # 5. Android App: Código Kotlin
    "android-app/app/src/main/java/com/transporte/widget/TransporteWidget.kt": f"""package com.transporte.widget

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

class TransporteWidget : AppWidgetProvider() {{

    companion object {{
        private const val ACTION_REFRESH = "com.transporte.widget.REFRESH"
        private const val JSON_URL = "https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/status.json"
    }}

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {{
        for (id in appWidgetIds) {{
            setupClick(context, id, appWidgetManager)
            actualizar(context, appWidgetManager, id)
        }}
    }}

    override fun onReceive(context: Context, intent: Intent) {{
        super.onReceive(context, intent)
        if (intent.action == ACTION_REFRESH) {{
            val manager = AppWidgetManager.getInstance(context)
            val ids = manager.getAppWidgetIds(ComponentName(context, TransporteWidget::class.java))
            for (id in ids) {{
                actualizar(context, manager, id)
            }}
        }}
    }}

    private fun setupClick(context: Context, widgetId: Int, manager: AppWidgetManager) {{
        val views = RemoteViews(context.packageName, R.layout.widget_layout)
        val intent = Intent(context, TransporteWidget::class.java).apply {{
            action = ACTION_REFRESH
        }}
        val pendingIntent = PendingIntent.getBroadcast(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_root, pendingIntent)
        manager.updateAppWidget(widgetId, views)
    }}

    private fun actualizar(context: Context, manager: AppWidgetManager, widgetId: Int) {{
        val views = RemoteViews(context.packageName, R.layout.widget_layout)
        views.setTextViewText(R.id.txt_hora, "Cargando...")
        manager.updateAppWidget(widgetId, views)

        thread {{
            try {{
                val url = URL(JSON_URL)
                val conn = url.openConnection() as HttpURLConnection
                conn.connectTimeout = 6000
                conn.readTimeout = 6000
                conn.useCaches = false

                val text = conn.inputStream.bufferedReader().use {{ it.readText() }}
                val json = JSONObject(text)

                val subte = json.getJSONObject("subte_c").getString("estado")
                val roca = json.getJSONObject("tren_roca").getString("estado")
                val hora = json.getString("actualizado")

                views.setTextViewText(R.id.txt_subte, "Subte C: $subte")
                views.setTextViewText(R.id.txt_roca, "Roca Korn: $roca")
                views.setTextViewText(R.id.txt_hora, "Actualizado: $hora hs")
            }} catch (e: Exception) {{
                views.setTextViewText(R.id.txt_hora, "Error al conectar (toca aquí)")
            }}
            manager.updateAppWidget(widgetId, views)
        }}
    }}
}}
""",

    # 6. .gitignore y README inicial
    ".gitignore": """status.json
.gradle/
build/
android-app/app/build/
*.iml
.idea/
local.properties
__pycache__/
*.pyc
""",
    "README.md": "# Widget Transporte (Subte C + Tren Roca Korn)\nProyecto automatizado con GitHub Actions y Kotlin."
}

def crear_estructura():
    base_dir = os.getcwd()
    for ruta_relativa, contenido in ARCHIVOS.items():
        ruta_completa = os.path.join(base_dir, ruta_relativa)
        os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write(contenido)
        print(f"Creado: {ruta_relativa}")

    print("\nEstructura generada exitosamente.")
    print("Ya puedes ejecutar: git init, agregar los archivos y subir a GitHub.")

if __name__ == "__main__":
    crear_estructura()