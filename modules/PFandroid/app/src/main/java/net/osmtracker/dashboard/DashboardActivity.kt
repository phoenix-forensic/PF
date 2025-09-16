package net.osmtracker.dashboard

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.viewpager2.widget.ViewPager2
import io.socket.client.IO
import io.socket.client.Socket
import net.osmtracker.dashboard.events.NovoEvento
import org.greenrobot.eventbus.EventBus
import java.net.URISyntaxException

class DashboardActivity : AppCompatActivity() {
    private lateinit var socket: Socket

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_dashboard)

        val pager: ViewPager2 = findViewById(R.id.dashboardPager)
        pager.adapter = DashboardPagerAdapter(this)

        try {
            socket = IO.socket("http://10.0.2.2:5000")
            socket.connect()
            socket.on("novo_evento") { args ->
                val payload = args.firstOrNull()
                if (payload is org.json.JSONObject) {
                    val lat = payload.optDouble("lat", 0.0)
                    val lon = payload.optDouble("lon", 0.0)
                    val risk = payload.optString("risk", "low")
                    EventBus.getDefault().post(NovoEvento(lat, lon, risk))
                }
            }
        } catch (e: URISyntaxException) {
            e.printStackTrace()
        }
    }

    override fun onDestroy() {
        if (this::socket.isInitialized) {
            socket.disconnect()
            socket.off("novo_evento")
        }
        super.onDestroy()
    }
}
