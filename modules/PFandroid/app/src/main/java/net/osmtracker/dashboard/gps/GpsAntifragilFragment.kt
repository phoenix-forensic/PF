package net.osmtracker.dashboard.gps

import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.fragment.app.Fragment
import net.osmtracker.dashboard.R
import net.osmtracker.dashboard.events.NovoEvento
import org.greenrobot.eventbus.EventBus
import org.greenrobot.eventbus.Subscribe
import org.greenrobot.eventbus.ThreadMode

class GpsAntifragilFragment : Fragment(R.layout.fragment_gps_antifragil) {

    private var anomalyCounter = 0

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        updateStatus(view, "Aguardando telemetria...")
    }

    override fun onStart() {
        super.onStart()
        EventBus.getDefault().register(this)
    }

    override fun onStop() {
        EventBus.getDefault().unregister(this)
        super.onStop()
    }

    @Subscribe(threadMode = ThreadMode.MAIN)
    fun onNovoEvento(event: NovoEvento) {
        val view = view ?: return
        val statusText = view.findViewById<TextView>(R.id.statusText)
        val anomalyText = view.findViewById<TextView>(R.id.anomalyCounter)

        val coordinates = "${event.lat}, ${event.lon}"
        statusText.text = getString(R.string.event_received, coordinates, event.risk)

        if (event.risk == "spoof") {
            anomalyCounter += 1
        }
        anomalyText.text = getString(R.string.anomaly_counter, anomalyCounter)
    }

    private fun updateStatus(view: View, message: String) {
        val statusText = view.findViewById<TextView>(R.id.statusText)
        statusText.text = message
    }
}
