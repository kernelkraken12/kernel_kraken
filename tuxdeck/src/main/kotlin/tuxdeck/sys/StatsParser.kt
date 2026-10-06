/*
 * TuxDeck — StatsParser
 *
 * Extracted VERBATIM from app/src/main/java/com/yurii/tuxdeck/sys/Stats.kt, where the parsing lived
 * inline inside `fetchStats(conn)`. Reason for the extraction: inline logic behind a live SSH call
 * cannot be unit-tested, and a project that ships no tests cannot honestly claim rule #8 (TESTED).
 *
 * The functions here are PURE: String in, data out. No Android, no sshj, no coroutines, no I/O.
 * That is deliberate — it is what lets these tests run anywhere a JVM exists, with no Android SDK.
 *
 * TWO DECLARED BEHAVIOUR CHANGES vs the original (both listed in CHECKLIST.md, both covered by tests):
 *   1. cpuTotal() excludes guest (field 8) and guest_nice (field 9). /proc/stat counts BOTH of them
 *      inside user/nice already, so the original `p.sum()` double-counted them and skewed CPU%.
 *   2. buildMagicPacket() returns null for a malformed MAC. The original called toInt(16) directly and
 *      threw NumberFormatException out of a UI path.
 */
package tuxdeck.sys

/** One /proc/stat `cpu ` sample: summed jiffies and the idle part (idle + iowait). */
data class CpuSample(val total: Long, val idle: Long) {
    fun pct(other: CpuSample): Float {
        val dTotal = total - other.total
        val dIdle = idle - other.idle
        if (dTotal <= 0) return 0f
        return ((1f - dIdle.toFloat() / dTotal) * 100f).coerceIn(0f, 100f)
    }
}

data class DiskInfo(val mount: String, val usedPct: Int, val used: Long, val total: Long)
data class ServiceInfo(val unit: String, val load: String, val sub: String, val desc: String)

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

object StatsParser {

    /** `([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}` — the app's own MAC shape test. */
    val MAC_RE = Regex("([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}")

    /**
     * Section splitter, verbatim: everything after `tag` up to the next `__`, trimmed.
     * NOTE the original: a value that itself contains `__` truncates here. Kept as-is (behaviour
     * preserved) and exercised by a test that documents it.
     */
    fun section(text: String, tag: String): String =
        text.substringAfter(tag, "").substringBefore("__").trim()

    /** The two `cpu ` lines the remote script prints, in order. */
    fun cpuLines(text: String): List<String> =
        text.split("__")[0].split("\n").filter { it.startsWith("cpu ") }

    /**
     * One `cpu` line → CpuSample. Fields: user nice system idle iowait irq softirq steal guest
     * guest_nice. Needs at least 5 numeric fields (the original's guard).
     *
     * DECLARED FIX: guest/guest_nice (indices 8,9) are excluded from the total because the kernel
     * already includes them in user/nice. Idle = idle + iowait (original behaviour, kept).
     */
    fun parseCpuLine(line: String): CpuSample? {
        val p = line.trim().split(Regex("\\s+")).drop(1).mapNotNull { it.toLongOrNull() }
        if (p.size < 5) return null
        val total = p.take(8).sum()          // was p.sum() — see fix 1
        return CpuSample(total, p[3] + p[4])
    }

    /** CPU% between two samples; 0f when they are not two usable samples or the clock did not move. */
    fun cpuPercent(c1: CpuSample?, c2: CpuSample?): Float =
        if (c1 != null && c2 != null) c2.pct(c1) else 0f

    /** MemTotal / MemAvailable in kB as printed by /proc/meminfo; 0L when absent. */
    fun parseMemKb(memSection: String): Pair<Long, Long> {
        val total = Regex("MemTotal:\\s+(\\d+)").find(memSection)?.groupValues?.get(1)?.toLongOrNull() ?: 0L
        val avail = Regex("MemAvailable:\\s+(\\d+)").find(memSection)?.groupValues?.get(1)?.toLongOrNull() ?: 0L
        return total to avail
    }

    /** First three floats of /proc/loadavg. */
    fun parseLoads(loadSection: String): List<Float> {
        val line = loadSection.split("\n").firstOrNull() ?: ""
        return line.trim().split(Regex("\\s+")).take(3).mapNotNull { it.toFloatOrNull() }
    }

    /**
     * `df -P` rows → DiskInfo. Fields: Filesystem 1024-blocks Used Available Capacity% Mounted-on.
     * The header row is rejected because its 5th field ("Capacity") does not end in `%`.
     * Row needs >= 6 fields; used/total are converted kB→bytes (×1024); total>0 filter kept.
     */
    fun parseDisks(diskSection: String): List<DiskInfo> =
        diskSection.split("\n").mapNotNull { line ->
            val p = line.trim().split(Regex("\\s+"))
            if (p.size < 6 || !p[4].endsWith("%")) return@mapNotNull null
            val pct = p[4].trimEnd('%').toIntOrNull() ?: return@mapNotNull null
            DiskInfo(
                mount = p[5],
                usedPct = pct,
                used = (p[2].toLongOrNull() ?: 0L) * 1024,
                total = (p[1].toLongOrNull() ?: 0L) * 1024,
            )
        }.filter { it.total > 0 }

    /** Mem used as a percentage; 0f when MemTotal is unknown (original guard). */
    fun memUsedPct(memTotalKb: Long, memAvailKb: Long): Float =
        if (memTotalKb > 0) ((memTotalKb - memAvailKb).toFloat() / memTotalKb * 100f) else 0f

    /**
     * `systemctl list-units --plain` rows → ServiceInfo(unit, load, sub, desc).
     * limit=5 keeps the description whole; the ACTIVE column (p[2]) is intentionally dropped —
     * the app colours by SUB (p[3]), which is the original behaviour.
     */
    fun parseServices(runningPart: String): List<ServiceInfo> =
        runningPart.split("\n").mapNotNull { line ->
            val p = line.trim().split(Regex("\\s+"), limit = 5)
            if (p.size < 4 || p[0].isBlank()) return@mapNotNull null
            ServiceInfo(p[0], p[1], p[3], p.getOrElse(4) { "" })
        }

    /** Count of failed units — the app counts lines that mention `.service`. */
    fun countFailed(failedPart: String): Int =
        failedPart.split("\n").count { it.contains(".service") }

    fun isMac(s: String): Boolean = s.matches(MAC_RE)

    /** Assemble everything from one captured script output (the shape fetchStats sends). */
    fun parseAll(text: String): Stats {
        val c1 = cpuLines(text).getOrNull(0)?.let(::parseCpuLine)
        val c2 = cpuLines(text).getOrNull(1)?.let(::parseCpuLine)
        val (memTotal, memAvail) = parseMemKb(section(text, "__MEM"))
        val loads = parseLoads(section(text, "__LOAD"))
        return Stats(
            cpuPct = cpuPercent(c1, c2),
            memUsedPct = memUsedPct(memTotal, memAvail),
            memUsed = (memTotal - memAvail) * 1024,
            memTotal = memTotal * 1024,
            load1 = loads.getOrElse(0) { 0f },
            load5 = loads.getOrElse(1) { 0f },
            load15 = loads.getOrElse(2) { 0f },
            uptime = section(text, "__UP").lines().firstOrNull()?.trim() ?: "",
            hostname = section(text, "__HN").lines().firstOrNull()?.trim() ?: "",
            disks = parseDisks(section(text, "__DISK")),
        )
    }
}
