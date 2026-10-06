package com.yurii.tuxdeck.sys

import com.yurii.tuxdeck.ssh.SshConn
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

data class CpuSample(val total: Long, val idle: Long) {
    fun pct(other: CpuSample): Float {
        val dTotal = total - other.total
        val dIdle = idle - other.idle
        if (dTotal <= 0) return 0f
        return ((1f - dIdle.toFloat() / dTotal) * 100f).coerceIn(0f, 100f)
    }
}

data class DiskInfo(val mount: String, val usedPct: Int, val used: Long, val total: Long)

data class Stats(
    val cpuPct: Float,
    val memUsedPct: Float,
    val memUsed: Long,
    val memTotal: Long,
    val load1: Float,
    val load5: Float,
    val load15: Float,
    val uptime: String,
    val hostname: String,
    val disks: List<DiskInfo>,
    val rawCpu: Float = 0f,
)

/** Grabs everything in ONE ssh round trip. */
suspend fun fetchStats(conn: SshConn): Stats = withContext(Dispatchers.IO) {
    val script = """
        sh -c 'grep "^cpu " /proc/stat; sleep 0.4; grep "^cpu " /proc/stat;
        echo __MEM; grep -E "MemTotal|MemAvailable" /proc/meminfo;
        echo __LOAD; cat /proc/loadavg;
        echo __UP; uptime -p 2>/dev/null || uptime;
        echo __HN; hostname;
        echo __DISK; df -P -x tmpfs -x devtmpfs -x squashfs -x efivarfs 2>/dev/null'
    """.replace("\n", " ").trimIndent().replace(Regex("\\s+"), " ")

    val r = conn.exec(script, 15)
    val text = r.stdout

    fun section(tag: String): String =
        text.substringAfter(tag, "").substringBefore("__").trim()

    // CPU: two /proc/stat lines
    val cpuLines = text.split("__")[0].split("\n").filter { it.startsWith("cpu ") }
    fun parseCpu(line: String): CpuSample? {
        val p = line.trim().split(Regex("\\s+")).drop(1).mapNotNull { it.toLongOrNull() }
        if (p.size < 5) return null
        return CpuSample(p.sum(), p[3] + p[4]) // idle + iowait
    }
    val c1 = cpuLines.getOrNull(0)?.let(::parseCpu)
    val c2 = cpuLines.getOrNull(1)?.let(::parseCpu)
    val cpu = if (c1 != null && c2 != null) c2.pct(c1) else 0f

    val mem = section("__MEM")
    val memTotal = Regex("MemTotal:\\s+(\\d+)").find(mem)?.groupValues?.get(1)?.toLongOrNull() ?: 0L
    val memAvail = Regex("MemAvailable:\\s+(\\d+)").find(mem)?.groupValues?.get(1)?.toLongOrNull() ?: 0L

    val loadLine = section("__LOAD").split("\n").firstOrNull() ?: ""
    val loads = loadLine.trim().split(Regex("\\s+")).take(3).mapNotNull { it.toFloatOrNull() }

    val disks = section("__DISK").split("\n").mapNotNull { line ->
        val p = line.trim().split(Regex("\\s+"))
        // df -P: Filesystem 1024-blocks Used Available Capacity% Mounted-on
        if (p.size < 6 || !p[4].endsWith("%")) return@mapNotNull null
        val pct = p[4].trimEnd('%').toIntOrNull() ?: return@mapNotNull null
        DiskInfo(mount = p[5], usedPct = pct, used = (p[2].toLongOrNull() ?: 0L) * 1024, total = (p[1].toLongOrNull() ?: 0L) * 1024)
    }.filter { it.total > 0 }

    Stats(
        cpuPct = cpu,
        memUsedPct = if (memTotal > 0) ((memTotal - memAvail).toFloat() / memTotal * 100f) else 0f,
        memUsed = (memTotal - memAvail) * 1024,
        memTotal = memTotal * 1024,
        load1 = loads.getOrElse(0) { 0f },
        load5 = loads.getOrElse(1) { 0f },
        load15 = loads.getOrElse(2) { 0f },
        uptime = section("__UP").lines().firstOrNull()?.trim() ?: "",
        hostname = section("__HN").lines().firstOrNull()?.trim() ?: "",
        disks = disks,
    )
}

data class ServiceInfo(val unit: String, val load: String, val sub: String, val desc: String)

suspend fun fetchServices(conn: SshConn): Pair<List<ServiceInfo>, Int> = withContext(Dispatchers.IO) {
    val r = conn.exec(
        "systemctl list-units --type=service --no-pager --no-legend --plain | head -80; echo __FAILED; systemctl --failed --no-pager --no-legend --plain | head -10",
        15
    )
    val text = r.stdout
    val failedIdx = text.indexOf("__FAILED")
    val runningPart = if (failedIdx >= 0) text.substring(0, failedIdx) else text
    val failedPart = if (failedIdx >= 0) text.substring(failedIdx + "__FAILED".length) else ""

    val services = runningPart.split("\n").mapNotNull { line ->
        val p = line.trim().split(Regex("\\s+"), limit = 5)
        if (p.size < 4 || p[0].isBlank()) return@mapNotNull null
        ServiceInfo(p[0], p[1], p[3], p.getOrElse(4) { "" })
    }.filter { it.sub != "running" || true } // keep all; UI colors by state

    val failed = failedPart.split("\n").count { it.contains(".service") }
    services to failed
}

suspend fun fetchJournal(conn: SshConn, lines: Int = 120): String = withContext(Dispatchers.IO) {
    val r = conn.exec("journalctl -n $lines --no-pager -o short 2>/dev/null || echo '(journal not readable for this user)'", 15)
    r.stdout
}

suspend fun primaryMac(conn: SshConn): String? = withContext(Dispatchers.IO) {
    val r = conn.exec("ip -o link show | sed -n 's/.*link\\/ether \\([0-9a-f:]*\\).*/\\1/p' | head -1", 8)
    r.stdout.trim().takeIf { it.matches(Regex("([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}")) }
}
