package com.yurii.tuxdeck

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.Bolt
import androidx.compose.material.icons.rounded.Delete
import androidx.compose.material.icons.rounded.Key
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.SettingsPower
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.yurii.tuxdeck.ssh.Connections
import com.yurii.tuxdeck.ssh.Host
import com.yurii.tuxdeck.ssh.HostStore
import com.yurii.tuxdeck.ssh.WakeOnLan
import com.yurii.tuxdeck.sys.Stats
import com.yurii.tuxdeck.sys.ServiceInfo
import com.yurii.tuxdeck.sys.fetchJournal
import com.yurii.tuxdeck.sys.fetchServices
import com.yurii.tuxdeck.sys.fetchStats
import com.yurii.tuxdeck.sys.primaryMac
import com.yurii.tuxdeck.ui.Amber
import com.yurii.tuxdeck.ui.Bg
import com.yurii.tuxdeck.ui.DeckTheme
import com.yurii.tuxdeck.ui.FluxBlue
import com.yurii.tuxdeck.ui.Green
import com.yurii.tuxdeck.ui.GaugeRing
import com.yurii.tuxdeck.ui.Ink
import com.yurii.tuxdeck.ui.InkLo
import com.yurii.tuxdeck.ui.LedAmber
import com.yurii.tuxdeck.ui.LedReadout
import com.yurii.tuxdeck.ui.LedRed
import com.yurii.tuxdeck.ui.Mono
import com.yurii.tuxdeck.ui.Panel
import com.yurii.tuxdeck.ui.PanelHi
import com.yurii.tuxdeck.ui.Red
import com.yurii.tuxdeck.ui.FluxCapacitor
import com.yurii.tuxdeck.ui.Steel
import com.yurii.tuxdeck.ui.SteelDim
import com.yurii.tuxdeck.ui.TermCard
import com.yurii.tuxdeck.ui.brailleSpark
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.UUID

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            DeckTheme { Deck() }
        }
    }
}

// ---------------------------------------------------------------- navigation

private sealed interface Screen {
    data object Hosts : Screen
    data class Cockpit(val hostId: String) : Screen
}

@Composable
fun Deck() {
    val context = LocalContext.current
    val hosts = remember { mutableStateListOf<Host>().apply { addAll(HostStore.load(context)) } }
    var screen by remember { mutableStateOf<Screen>(Screen.Hosts) }

    fun persist() = HostStore.save(context, hosts)

    BackHandler(enabled = screen is Screen.Cockpit) {
        (screen as? Screen.Cockpit)?.let { Connections.drop(it.hostId) }
        screen = Screen.Hosts
    }

    when (val s = screen) {
        Screen.Hosts -> HostsScreen(
            hosts = hosts,
            onOpen = { screen = Screen.Cockpit(it) },
            onChanged = { persist() },
        )
        is Screen.Cockpit -> {
            val host = hosts.firstOrNull { it.id == s.hostId }
            if (host == null) screen = Screen.Hosts
            else CockpitScreen(host = host, onBack = {
                Connections.drop(host.id)
                screen = Screen.Hosts
            }, onDelete = {
                Connections.drop(host.id)
                hosts.removeAll { it.id == host.id }
                persist()
                screen = Screen.Hosts
            }, onUpdated = { persist() })
        }
    }
}

// ---------------------------------------------------------------- hosts list

@Composable
fun HostsScreen(
    hosts: MutableList<Host>,
    onOpen: (String) -> Unit,
    onChanged: () -> Unit,
) {
    var adding by remember { mutableStateOf(false) }

    Column(
        Modifier
            .fillMaxSize()
            .background(Bg)
            .statusBarsPadding()
            .navigationBarsPadding()
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    "TUXDECK",
                    style = MaterialTheme.typography.headlineMedium,
                    color = Steel,
                    letterSpacing = 3.sp,
                )
                Text(
                    "roads? where we're going, we don't need roads.",
                    style = MaterialTheme.typography.labelSmall,
                    color = InkLo,
                )
            }
            Box(
                Modifier
                    .size(44.dp)
                    .clip(CircleShape)
                    .background(PanelHi)
                    .border(1.dp, FluxBlue.copy(alpha = 0.5f), CircleShape)
                    .clickable { adding = true },
                contentAlignment = Alignment.Center,
            ) {
                Icon(Icons.Rounded.Add, "add host", tint = FluxBlue)
            }
        }

        if (hosts.isEmpty()) {
            Column(
                Modifier
                    .fillMaxWidth()
                    .weight(1f),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Text(
                    "        _____\n     /     \\\n    | () () |\n     \\  ^  /\n      |||||\n      |||||",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Green,
                    lineHeight = 18.sp,
                    textAlign = TextAlign.Start,
                )
                Spacer(Modifier.height(18.dp))
                Text("no machines on the deck.", style = MaterialTheme.typography.bodyMedium, color = Ink)
                Text("add one — sshd is probably already listening.", style = MaterialTheme.typography.labelSmall, color = InkLo)
            }
        } else {
            LazyColumn(Modifier.weight(1f)) {
                items(hosts, key = { it.id }) { h ->
                    HostCard(
                        host = h,
                        onOpen = { onOpen(h.id) },
                        onDelete = { hosts.removeAll { it.id == h.id }; onChanged() },
                        onWake = {
                            h.mac?.let { mac ->
                                kotlinx.coroutines.GlobalScope.launch { WakeOnLan.wake(mac) }
                            }
                        },
                    )
                }
            }
        }

        Row(
            Modifier
                .fillMaxWidth()
                .padding(14.dp),
            horizontalArrangement = Arrangement.Center,
        ) {
            Text("TUXDECK", style = MaterialTheme.typography.labelSmall, color = InkLo, letterSpacing = 2.sp)
            Text("  ·  ", style = MaterialTheme.typography.labelSmall, color = SteelDim)
            Text("OUTATIME", style = MaterialTheme.typography.labelSmall, color = Amber, letterSpacing = 2.sp)
        }
    }

    if (adding) {
        AddHostDialog(
            onDismiss = { adding = false },
            onAdd = { h ->
                hosts.add(h)
                onChanged()
                adding = false
                onOpen(h.id)
            },
        )
    }
}

@Composable
fun HostCard(
    host: Host,
    onOpen: () -> Unit,
    onDelete: () -> Unit,
    onWake: () -> Unit,
) {
    var probing by remember { mutableStateOf(false) }
    var alive by remember { mutableStateOf<Boolean?>(null) }

    // light liveness probe when card appears
    LaunchedEffect(host.id) {
        probing = true
        val conn = Connections.forHost(host)
        alive = try {
            kotlinx.coroutines.withTimeoutOrNull(6000) {
                withContext(Dispatchers.IO) {
                    val c = conn.ensure()
                    c.isConnected
                }
            } ?: false
        } catch (e: Exception) {
            false
        }
        probing = false
    }

    TermCard(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 14.dp, vertical = 6.dp)
            .clickable { onOpen() },
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // power LED
            val ledColor = when {
                probing == true -> Amber
                alive == true -> Green
                else -> Red
            }
            Box(
                Modifier
                    .size(12.dp)
                    .clip(CircleShape)
                    .background(ledColor)
            )
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(host.label, style = MaterialTheme.typography.titleMedium, color = Ink)
                Text(
                    "${host.user}@${host.hostname}:${host.port} · ${host.authLabel()}${if (host.mac != null) " · wol ✓" else ""}",
                    style = MaterialTheme.typography.labelSmall,
                    color = InkLo,
                )
            }
            if (alive == false && host.mac != null) {
                TextButton(onClick = onWake) {
                    Icon(Icons.Rounded.Bolt, null, tint = Amber, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("WAKE", style = MaterialTheme.typography.labelSmall, color = Amber)
                }
            }
            IconButton(onClick = onDelete) {
                Icon(Icons.Rounded.Delete, "delete", tint = InkLo, modifier = Modifier.size(18.dp))
            }
        }
    }
}

@Composable
fun AddHostDialog(onDismiss: () -> Unit, onAdd: (Host) -> Unit) {
    val context = androidx.compose.ui.platform.LocalContext.current
    var label by remember { mutableStateOf("") }
    var hostname by remember { mutableStateOf("") }
    var port by remember { mutableStateOf("22") }
    var user by remember { mutableStateOf("yurii") }
    var password by remember { mutableStateOf("") }
    var keyText by remember { mutableStateOf<String?>(null) }

    val keyPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri != null) {
            context.contentResolver.openInputStream(uri)?.use { keyText = it.readBytes().toString(Charsets.UTF_8) }
        }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add host", color = Ink) },
        text = {
            Column {
                OutlinedTextField(label, { label = it }, label = { Text("label") }, singleLine = true)
                OutlinedTextField(hostname, { hostname = it }, label = { Text("hostname / IP") }, singleLine = true)
                OutlinedTextField(port, { port = it }, label = { Text("port") }, singleLine = true)
                OutlinedTextField(user, { user = it }, label = { Text("user") }, singleLine = true)
                OutlinedTextField(
                    password,
                    { password = it },
                    label = { Text("password (or import key below)") },
                    singleLine = true,
                )
                Spacer(Modifier.height(8.dp))
                TextButton(onClick = { keyPicker.launch(arrayOf("*/*")) }) {
                    Icon(Icons.Rounded.Key, null, tint = FluxBlue, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(6.dp))
                    Text(
                        if (keyText != null) "key imported ✓" else "import SSH key file",
                        color = FluxBlue,
                        style = MaterialTheme.typography.labelSmall,
                    )
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                if (hostname.isBlank() || user.isBlank()) return@TextButton
                onAdd(
                    Host(
                        id = UUID.randomUUID().toString(),
                        label = label.ifBlank { hostname },
                        hostname = hostname.trim(),
                        port = port.toIntOrNull() ?: 22,
                        user = user.trim(),
                        password = password.ifBlank { null },
                        privateKey = keyText,
                    )
                )
            }) { Text("Connect", color = Green) }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel", color = InkLo) } },
    )
}

// ---------------------------------------------------------------- cockpit

private enum class DeckTab(val label: String) { OVERVIEW("overview"), SERVICES("services"), JOURNAL("journal"), TERMINAL("terminal") }

@Composable
fun CockpitScreen(host: Host, onBack: () -> Unit, onDelete: () -> Unit, onUpdated: () -> Unit) {
    val scope = rememberCoroutineScope()
    var tab by remember { mutableStateOf(DeckTab.OVERVIEW) }

    // shared live state
    var online by remember { mutableStateOf<Boolean?>(null) }
    var lastError by remember { mutableStateOf<String?>(null) }
    var stats by remember { mutableStateOf<Stats?>(null) }
    val cpuHistory = remember { mutableStateListOf<Float>() }
    var services by remember { mutableStateOf<List<ServiceInfo>?>(null) }
    var failedCount by remember { mutableStateOf(0) }
    var journal by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    var toast by remember { mutableStateOf<String?>(null) }
    var powerMenu by remember { mutableStateOf(false) }
    var confirmAction by remember { mutableStateOf<String?>(null) }

    val conn = remember(host.id) { Connections.forHost(host) }

    // poller: stats every 3 s whenever we're on this screen
    DisposableEffect(host.id) {
        var job: Job? = null
        job = scope.launch {
            while (isActive) {
                try {
                    val s = fetchStats(conn)
                    stats = s
                    online = true
                    lastError = null
                    cpuHistory.add(s.cpuPct)
                    while (cpuHistory.size > 60) cpuHistory.removeAt(0)
                } catch (e: Exception) {
                    online = false
                    lastError = e.message ?: e.javaClass.simpleName
                }
                delay(3000)
            }
        }
        onDispose { job?.cancel() }
    }

    fun doAction(action: String) {
        scope.launch {
            busy = true
            try {
                when (action) {
                    "lock" -> { conn.exec("loginctl lock-session"); toast = "session locked [OK]" }
                    "suspend" -> {
                        conn.exec("systemctl suspend")
                        toast = "suspending… 1.21 GIGAWATTS"
                        online = false
                    }
                    "reboot" -> { conn.exec("systemctl reboot"); toast = "rebooting…"; online = false }
                    "poweroff" -> { conn.exec("systemctl poweroff"); toast = "powering off…"; online = false }
                    "fetch_mac" -> {
                        primaryMac(conn)?.let {
                            toast = "MAC: $it"
                        } ?: run { toast = "could not read MAC" }
                    }
                }
            } catch (e: Exception) {
                toast = "failed: ${e.message}"
            }
            busy = false
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .background(Bg)
            .statusBarsPadding()
            .navigationBarsPadding()
    ) {
        // header
        Row(
            Modifier
                .fillMaxWidth()
                .padding(horizontal = 8.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Rounded.ArrowBack, "back", tint = Ink)
            }
            Column(Modifier.weight(1f)) {
                Text(host.label, style = MaterialTheme.typography.titleLarge, color = Ink)
                Text(
                    when (online) {
                        true -> "${stats?.hostname ?: host.hostname} · live"
                        false -> "unreachable: ${lastError?.take(60) ?: "unknown"}"
                        null -> "probing…"
                    },
                    style = MaterialTheme.typography.labelSmall,
                    color = when (online) {
                        true -> Green
                        false -> Red
                        null -> InkLo
                    },
                )
            }
            if (busy) CircularProgressIndicator(color = Amber, modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
            IconButton(onClick = { powerMenu = true }) {
                Icon(Icons.Rounded.SettingsPower, "power menu", tint = Red)
            }
        }

        // TIME CIRCUITS — pinned live stats strip (LED style)
        Row(
            Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 2.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(Panel)
                .border(1.dp, SteelDim, RoundedCornerShape(8.dp))
                .padding(horizontal = 12.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            LedReadout("CPU", if (online == true) "%02d%%".format(stats?.cpuPct?.toInt() ?: 0) else "--%")
            LedReadout("MEM", if (online == true) "%02d%%".format(stats?.memUsedPct?.toInt() ?: 0) else "--%")
            LedReadout("LOAD", if (online == true) "%.2f".format(stats?.load1 ?: 0f) else "-.--")
            Column(horizontalAlignment = Alignment.End) {
                Text("FLUX", style = MaterialTheme.typography.labelSmall, color = InkLo)
                FluxCapacitor(Modifier.size(34.dp, 26.dp))
            }
        }

        // tabs
        TabRow(
            selectedTabIndex = tab.ordinal,
            containerColor = Panel,
            contentColor = Steel,
            indicator = { },
        ) {
            DeckTab.entries.forEach { t ->
                Tab(
                    selected = tab == t,
                    onClick = { tab = t },
                    text = {
                        Text(
                            t.label,
                            color = if (tab == t) Green else InkLo,
                            style = MaterialTheme.typography.labelMedium,
                            fontSize = 12.sp,
                            maxLines = 1,
                        )
                    },
                )
            }
        }

        Box(Modifier.fillMaxSize()) {
            when (tab) {
                DeckTab.OVERVIEW -> OverviewTab(stats, online, cpuHistory, host, { toast = it }, onUpdated)
                DeckTab.SERVICES -> ServicesTab(online, services, failedCount, { services = it.second; failedCount = it.first }, conn)
                DeckTab.JOURNAL -> JournalTab(online, journal, { journal = it }, conn)
                DeckTab.TERMINAL -> TerminalTab(host, conn, online)
            }

            toast?.let { msg ->
                Box(
                    Modifier
                        .align(Alignment.BottomCenter)
                        .padding(18.dp)
                        .clip(RoundedCornerShape(10.dp))
                        .background(PanelHi)
                        .border(1.dp, Amber.copy(alpha = 0.5f), RoundedCornerShape(10.dp))
                        .padding(horizontal = 14.dp, vertical = 10.dp)
                ) {
                    Text(msg, style = MaterialTheme.typography.labelSmall, color = Amber)
                }
                LaunchedEffect(msg) {
                    delay(2600)
                    toast = null
                }
            }
        }
    }

    // power menu dialog
    if (powerMenu) {
        AlertDialog(
            onDismissRequest = { powerMenu = false },
            title = { Text("Power — ${host.label}", color = Ink) },
            text = {
                Column {
                    PowerRow("Suspend (S3 sleep)", "safest off-switch; WoL can wake it") { confirmAction = "suspend" }
                    PowerRow("Reboot", "systemctl reboot") { confirmAction = "reboot" }
                    PowerRow("Power off", "full shutdown — needs physical power or WoL") { confirmAction = "poweroff" }
                    PowerRow("Lock session", "screensaver lock, stays on") { confirmAction = "lock" }
                }
            },
            confirmButton = {},
            dismissButton = { TextButton(onClick = { powerMenu = false }) { Text("Close", color = InkLo) } },
        )
    }

    confirmAction?.let { action ->
        AlertDialog(
            onDismissRequest = { confirmAction = null },
            title = { Text("Confirm: $action?", color = Red) },
            text = { Text("This runs on ${host.label} right now.", style = MaterialTheme.typography.bodySmall, color = InkLo) },
            confirmButton = {
                TextButton(onClick = {
                    confirmAction = null
                    powerMenu = false
                    doAction(action)
                }) { Text("Do it", color = Red) }
            },
            dismissButton = { TextButton(onClick = { confirmAction = null }) { Text("Cancel", color = InkLo) } },
        )
    }
}

@Composable
private fun PowerRow(label: String, sub: String, onClick: () -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .clickable { onClick() }
            .padding(vertical = 8.dp, horizontal = 4.dp)
    ) {
        Text(label, style = MaterialTheme.typography.bodyLarge, color = Ink)
        Text(sub, style = MaterialTheme.typography.labelSmall, color = InkLo)
    }
}

// ---------------------------------------------------------------- overview

@Composable
fun OverviewTab(
    stats: Stats?,
    online: Boolean?,
    cpuHistory: List<Float>,
    host: Host,
    onToast: (String) -> Unit,
    onUpdated: () -> Unit,
) {
    val scope = rememberCoroutineScope()

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(14.dp),
    ) {
        // HERO POWER BUTTON — the DeLorean ignition
        Box(
            Modifier
                .fillMaxWidth()
                .aspectRatio(2.1f)
                .clip(RoundedCornerShape(14.dp))
                .background(Panel)
                .border(1.dp, SteelDim, RoundedCornerShape(14.dp)),
            contentAlignment = Alignment.Center,
        ) {
            val pulse = rememberInfiniteTransition(label = "power").animateFloat(
                initialValue = 0.92f,
                targetValue = 1.05f,
                animationSpec = infiniteRepeatable(tween(1200), RepeatMode.Reverse),
                label = "powerPulse",
            )
            val isOn = online == true
            val glowColor = when (online) {
                true -> Green
                false -> FluxBlue
                null -> SteelDim
            }
            Box(
                Modifier
                    .size(120.dp)
                    .scale(if (isOn) 1f else pulse.value)
                    .clip(CircleShape)
                    .background(Brush.radialGradient(listOf(glowColor.copy(alpha = 0.22f), Color.Transparent)))
                    .border(2.dp, glowColor, CircleShape)
                    .clickable {
                        if (isOn) {
                            onToast("machine is on — power icon (top right) for menu")
                        } else {
                            host.mac?.let { mac ->
                                scope.launch {
                                    onToast("sending 1.21 GIGAWATTS → ${host.label}…")
                                    WakeOnLan.wake(mac)
                                }
                            } ?: onToast("no MAC stored yet — connect once and it's captured")
                        }
                    },
                contentAlignment = Alignment.Center,
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        androidx.compose.material.icons.Icons.Rounded.SettingsPower,
                        contentDescription = "power",
                        tint = glowColor,
                        modifier = Modifier.size(46.dp),
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        when (online) {
                            true -> "ONLINE"
                            false -> if (host.mac != null) "TAP TO WAKE" else "OFFLINE"
                            null -> "PROBING…"
                        },
                        style = MaterialTheme.typography.labelSmall,
                        color = glowColor,
                    )
                }
            }
            if (isOn) {
                Text(
                    "power menu: top-right icon",
                    style = MaterialTheme.typography.labelSmall,
                    color = InkLo,
                    modifier = Modifier.align(Alignment.BottomCenter).padding(bottom = 10.dp),
                )
            }
        }

        Spacer(Modifier.height(14.dp))

        // gauges
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly,
        ) {
            GaugeBox("CPU", (stats?.cpuPct ?: 0f) / 100f, "%d%%".format(stats?.cpuPct?.toInt() ?: 0), Green, Modifier.weight(1f))
            GaugeBox("MEMORY", (stats?.memUsedPct ?: 0f) / 100f, "%d%%".format(stats?.memUsedPct?.toInt() ?: 0), Amber, Modifier.weight(1f))
        }
        Spacer(Modifier.height(10.dp))

        TermCard(title = "CPU HISTORY") {
            Text(
                brailleSpark(cpuHistory),
                style = MaterialTheme.typography.bodyMedium,
                color = Green,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                fontSize = 13.sp,
            )
        }
        Spacer(Modifier.height(10.dp))

        TermCard(title = "SYSTEM") {
            Column(Modifier.padding(12.dp)) {
                KV("hostname", stats?.hostname ?: "—")
                KV("uptime", stats?.uptime?.ifBlank { "—" } ?: "—")
                KV("load", stats?.let { "%.2f  %.2f  %.2f".format(it.load1, it.load5, it.load15) } ?: "—")
                KV("memory", stats?.let { "%s / %s".format(fmtB(it.memUsed), fmtB(it.memTotal)) } ?: "—")
            }
        }
        Spacer(Modifier.height(10.dp))

        TermCard(title = "DISKS") {
            Column(Modifier.padding(12.dp)) {
                if (stats?.disks.isNullOrEmpty()) {
                    Text("—", color = InkLo, style = MaterialTheme.typography.bodySmall)
                }
                stats?.disks?.forEach { d ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .padding(vertical = 3.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            d.mount,
                            style = MaterialTheme.typography.labelSmall,
                            color = Ink,
                            modifier = Modifier.width(120.dp),
                            maxLines = 1,
                        )
                        Box(
                            Modifier
                                .weight(1f)
                                .height(8.dp)
                                .clip(RoundedCornerShape(4.dp))
                                .background(PanelHi)
                        ) {
                            Box(
                                Modifier
                                    .fillMaxWidth(d.usedPct / 100f)
                                    .height(8.dp)
                                    .clip(RoundedCornerShape(4.dp))
                                    .background(if (d.usedPct > 85) Red else Green)
                            )
                        }
                        Spacer(Modifier.width(8.dp))
                        Text(
                            "${d.usedPct}%",
                            style = MaterialTheme.typography.labelSmall,
                            color = InkLo,
                        )
                    }
                }
            }
        }
        Spacer(Modifier.height(20.dp))
    }
}

@Composable
private fun GaugeBox(label: String, fraction: Float, value: String, color: Color, modifier: Modifier = Modifier) {
    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.size(96.dp)) {
            GaugeRing(fraction, label, value, Modifier.fillMaxSize(), color = color)
            Text(value, style = MaterialTheme.typography.titleMedium, color = Ink)
        }
        Spacer(Modifier.height(4.dp))
        Text(label, style = MaterialTheme.typography.labelSmall, color = InkLo)
    }
}

@Composable
private fun KV(k: String, v: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
        Text(k, style = MaterialTheme.typography.labelSmall, color = InkLo, modifier = Modifier.width(90.dp))
        Text(v, style = MaterialTheme.typography.bodySmall, color = Ink)
    }
}

private fun fmtB(n: Long): String = when {
    n < 1024L * 1024 -> "%.0f MB".format(n / 1024f / 1024f)
    n < 1024L * 1024 * 1024 -> "%.1f GB".format(n / 1024f / 1024f / 1024f)
    else -> "%.1f GB".format(n / 1024f / 1024f / 1024f)
}

// ---------------------------------------------------------------- services

@Composable
fun ServicesTab(
    online: Boolean?,
    services: List<ServiceInfo>?,
    failed: Int,
    onLoaded: (Pair<Int, List<ServiceInfo>>) -> Unit,
    conn: com.yurii.tuxdeck.ssh.SshConn,
) {
    LaunchedEffect(online) {
        if (online == true && services == null) {
            try {
                val (list, f) = fetchServices(conn)
                onLoaded(f to list)
            } catch (e: Exception) { }
        }
    }
    Column(
        Modifier
            .fillMaxSize()
            .padding(14.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("systemd units", style = MaterialTheme.typography.titleMedium, color = Ink)
            Spacer(Modifier.width(10.dp))
            if (failed > 0) {
                Text("$failed failed", style = MaterialTheme.typography.labelSmall, color = Red)
            } else if (services != null) {
                Text("0 failed", style = MaterialTheme.typography.labelSmall, color = Green)
            }
        }
        Spacer(Modifier.height(8.dp))
        if (services == null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text(if (online == false) "host offline" else "reading units…", color = InkLo)
            }
        } else {
            LazyColumn {
                items(services, key = { it.unit }) { s ->
                    val stateColor = when {
                        s.sub == "running" -> Green
                        s.sub == "exited" -> InkLo
                        s.sub == "failed" -> Red
                        else -> Amber
                    }
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .padding(vertical = 5.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Box(
                            Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(stateColor)
                        )
                        Spacer(Modifier.width(10.dp))
                        Column(Modifier.weight(1f)) {
                            Text(s.unit, style = MaterialTheme.typography.bodySmall, color = Ink, maxLines = 1)
                            if (s.desc.isNotBlank()) {
                                Text(
                                    s.desc,
                                    style = MaterialTheme.typography.labelSmall,
                                    color = InkLo,
                                    maxLines = 1,
                                )
                            }
                        }
                        Text(s.sub, style = MaterialTheme.typography.labelSmall, color = stateColor)
                    }
                }
            }
        }
    }
}

// ---------------------------------------------------------------- journal

@Composable
fun JournalTab(online: Boolean?, journal: String?, onLoaded: (String) -> Unit, conn: com.yurii.tuxdeck.ssh.SshConn) {
    LaunchedEffect(online) {
        if (online == true && journal == null) {
            try { onLoaded(fetchJournal(conn)) } catch (e: Exception) { }
        }
    }
    Column(Modifier.fillMaxSize().padding(14.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("journalctl · last 120", style = MaterialTheme.typography.titleMedium, color = Ink)
            Spacer(Modifier.width(10.dp))
            IconButton(onClick = {
                try { onLoaded("") } catch (_: Exception) {}
            }) {
                Icon(Icons.Rounded.Refresh, "reload", tint = InkLo, modifier = Modifier.size(18.dp))
            }
        }
        Spacer(Modifier.height(6.dp))
        TermCard(title = "/var/log/everything") {
            Box(
                Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState())
                    .heightIn(max = 560.dp)
                    .padding(10.dp)
            ) {
                SelectionContainer {
                    Text(
                        journal?.takeLast(6000)?.ifBlank { "loading…" } ?: "loading…",
                        style = MaterialTheme.typography.labelSmall,
                        color = Green,
                        fontSize = 10.sp,
                        lineHeight = 14.sp,
                    )
                }
            }
        }
    }
}

// ---------------------------------------------------------------- terminal

@Composable
fun TerminalTab(host: Host, conn: com.yurii.tuxdeck.ssh.SshConn, online: Boolean?) {
    val scope = rememberCoroutineScope()
    val lines = remember { mutableStateListOf<String>() }
    var input by remember { mutableStateOf("") }
    var starting by remember { mutableStateOf(false) }
    var shellHandle by remember { mutableStateOf<Any?>(null) }

    fun append(raw: String) {
        // strip ANSI/OSC escapes (incl. shell-integration OSC w/ BEL or ST terminator)
        val clean = raw
            .replace(Regex("\u001B\\][^\u0007\u001B]*(\u0007|\u001B\\\\)?"), "")
            .replace(Regex("\u001B\\[[0-9;?]*[a-zA-Z]"), "")
            .replace(Regex("\u001B[=><]"), "")
            .replace("\r", "")
        if (clean.isNotEmpty()) {
            clean.split("\n").forEach { l -> lines.add(l) }
            while (lines.size > 400) lines.removeAt(0)
        }
    }

    DisposableEffect(host.id) {
        var readerJob: Job? = null
        var started = false
        readerJob = scope.launch {
            starting = true
            try {
                val sh = conn.openShell()
                shellHandle = sh
                started = true
                append("\u001B[0m— tuxdeck shell on ${host.label} (PTY xterm-256color) —\n")
                while (isActive) {
                    val chunk = kotlinx.coroutines.withContext(Dispatchers.IO) {
                        kotlinx.coroutines.delay(80)
                        sh.readAvailable()
                    }
                    append(chunk)
                }
            } catch (e: Exception) {
                if (e !is CancellationException) append("!! shell: ${e.message}\n")
            } finally {
                starting = false
            }
        }
        onDispose {
            (shellHandle as? com.yurii.tuxdeck.ssh.SshConn.Shell)?.close()
        }
    }

    Column(Modifier.fillMaxSize()) {
        TermCard(
            title = "yurii@${host.hostname}:~",
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(10.dp),
            accent = Green,
        ) {
            LazyColumn(Modifier.fillMaxSize().padding(10.dp), reverseLayout = false) {
                items(lines.size) { i ->
                    Text(
                        lines[i],
                        style = MaterialTheme.typography.labelSmall,
                        color = if (lines[i].startsWith("—") || lines[i].startsWith("!!")) Amber else Green,
                        fontSize = 11.sp,
                        lineHeight = 15.sp,
                    )
                }
                item {
                    Text("_", style = MaterialTheme.typography.labelSmall, color = Green, fontSize = 11.sp)
                }
            }
        }

        Row(
            Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                "$ ",
                style = MaterialTheme.typography.bodyLarge,
                color = Green,
                fontFamily = Mono,
            )
            androidx.compose.material3.OutlinedTextField(
                value = input,
                onValueChange = { input = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("type a command…", style = MaterialTheme.typography.labelSmall, color = InkLo) },
                textStyle = MaterialTheme.typography.bodyMedium.copy(color = Ink),
                singleLine = true,
            )
            IconButton(onClick = {
                if (input.isNotBlank()) {
                    val cmd = input
                    input = ""
                    append("$ cmd\n")
                    scope.launch {
                        (shellHandle as? com.yurii.tuxdeck.ssh.SshConn.Shell)?.let { sh ->
                            kotlinx.coroutines.withContext(Dispatchers.IO) { sh.write(cmd) }
                        }
                    }
                }
            }) {
                Icon(Icons.Rounded.Bolt, "run", tint = Amber)
            }
        }
    }
}
