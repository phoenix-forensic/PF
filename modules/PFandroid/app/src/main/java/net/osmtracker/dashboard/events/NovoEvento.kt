package net.osmtracker.dashboard.events

data class NovoEvento(
    val lat: Double,
    val lon: Double,
    val risk: String
)
