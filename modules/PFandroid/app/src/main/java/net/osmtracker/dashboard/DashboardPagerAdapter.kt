package net.osmtracker.dashboard

import androidx.fragment.app.Fragment
import androidx.fragment.app.FragmentActivity
import androidx.viewpager2.adapter.FragmentStateAdapter
import net.osmtracker.dashboard.gps.GpsAntifragilFragment

class DashboardPagerAdapter(activity: FragmentActivity) : FragmentStateAdapter(activity) {
    private val pages: List<() -> Fragment> = listOf(
        { GpsAntifragilFragment() }
    )

    override fun getItemCount(): Int = pages.size

    override fun createFragment(position: Int): Fragment = pages[position].invoke()
}
