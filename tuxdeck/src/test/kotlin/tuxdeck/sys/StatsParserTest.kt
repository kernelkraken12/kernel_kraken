/*
 * TuxDeck — StatsParser tests.
 *
 * The fixture /cn-capture.txt is NOT invented: it is the verbatim stdout of the app's own remote
 * script (`grep ^cpu /proc/stat; sleep 0.4; grep ^cpu ...; echo __MEM; ... df -P ...`) captured from
 * a real host (cn, Debian/Proxmox) on 2026-10-06. So these tests pin behaviour against measured
 * reality rather than against an expectation someone typed.
 */
package tuxdeck.sys

import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class StatsParserTest {

    private fun fixture(name: String): String {
        val s = javaClass.getResourceAsStream("/$name")
        assertNotNull(s, "fixture /$name missing from the test classpath — the run is not valid")
        return s!!.readBytes().toString(Charsets.UTF_8)
    }

    // ---------- /proc/stat CPU ----------

    @Test
    fun `parses a real cpu line and excludes the guest fields`() {
        val line = "cpu  533301452 95413324 203649596 9871770397 45658906 0 6751293 0 24221520 0"
        val s = StatsParser.parseCpuLine(line)
        assertNotNull(s)
        // take(8) = user nice system idle iowait irq softirq steal — guest(24221520) and
        // guest_nice(0) are excluded because the kernel already counts them inside user/nice.
        assertEquals(533301452L + 95413324L + 203649596L + 9871770397L + 45658906L + 0L + 6751293L, s!!.total)
        assertEquals(9871770397L + 45658906L, s.idle)
    }

    @Test
    fun `a line with fewer than five numeric fields is rejected`() {
        assertNull(StatsParser.parseCpuLine("cpu  1 2 3"))
        assertNull(StatsParser.parseCpuLine("cpu"))
        assertNull(StatsParser.parseCpuLine("not a cpu line at all"))
    }

    @Test
    fun `cpu percent from the real captured pair of samples`() {
        val f = fixture("cn-capture.txt")
        val lines = StatsParser.cpuLines(f)
        assertEquals(2, lines.size, "the script prints exactly two cpu samples")
        val pct = StatsParser.cpuPercent(
            StatsParser.parseCpuLine(lines[0]),
            StatsParser.parseCpuLine(lines[1]),
        )
        // frozen fixture: dTotal 636, dIdle 480 → (1 - 480/636) * 100
        assertTrue(pct in 0f..100f, "cpu pct must be a percentage, got $pct")
        assertEquals(24.53f, pct, 0.5f, "expected ~24.5% from the captured samples, got $pct")
    }

    @Test
    fun `cpu percent is zero when the sample clock did not move`() {
        val same = CpuSample(1000L, 500L)
        assertEquals(0f, StatsParser.cpuPercent(same, same.copy()))
        assertEquals(0f, StatsParser.cpuPercent(null, same))
        assertEquals(0f, StatsParser.cpuPercent(same, null))
        assertEquals(0f, StatsParser.cpuPercent(null, null))
    }

    @Test
    fun `cpu percent is clamped into zero to one hundred`() {
        // idle delta larger than total delta → raw value below 0
        assertTrue(CpuSample(1000L, 900L).pct(CpuSample(10L, 10L)) >= 0f)
        // idle delta negative → raw value above 100
        assertTrue(CpuSample(10L, -50L).pct(CpuSample(100L, 90L)) <= 100f)
    }

    // ---------- section splitter ----------

    @Test
    fun `section returns the text between its tag and the next tag`() {
        val t = "__MEM\nMemTotal: 100 kB\n__LOAD\n1.0 2.0 3.0"
        assertEquals("MemTotal: 100 kB", StatsParser.section(t, "__MEM"))
        assertEquals("1.0 2.0 3.0", StatsParser.section(t, "__LOAD"))
        assertEquals("", StatsParser.section(t, "__NOPE"))
    }

    @Test
    fun `section truncates on a value that itself contains the tag prefix`() {
        // Documents the original behaviour: an embedded "__" ends the section early.
        assertEquals("abc", StatsParser.section("__MEM\nabc__def\n__LOAD", "__MEM"))
    }

    // ---------- memory ----------

    @Test
    fun `parses MemTotal and MemAvailable in kB from the fixture`() {
        val f = fixture("cn-capture.txt")
        val (total, avail) = StatsParser.parseMemKb(StatsParser.section(f, "__MEM"))
        assertTrue(total > 1_000_000L, "MemTotal should be a real host's memory, got $total")
        assertTrue(avail in 1L..total, "MemAvailable must sit between 1 and MemTotal, got $avail")
    }

    @Test
    fun `absent memory fields become zero and the percentage is guarded`() {
        assertEquals(0L to 0L, StatsParser.parseMemKb("nothing here"))
        assertEquals(0f, StatsParser.memUsedPct(0L, 0L))
        assertEquals(50f, StatsParser.memUsedPct(1000L, 500L), 0.001f)
    }

    // ---------- load ----------

    @Test
    fun `parses the first three floats of loadavg`() {
        assertEquals(listOf(1.5f, 2.25f, 3.0f), StatsParser.parseLoads("1.5 2.25 3.0 1/234 5678"))
    }

    @Test
    fun `a short or garbled loadavg yields fewer values and parseAll defaults to zero`() {
        assertEquals(listOf(0.5f), StatsParser.parseLoads("0.5"))
        assertEquals(0f, StatsParser.parseAll("").load1)
    }

    // ---------- df ----------

    @Test
    fun `parses real df rows and rejects the header`() {
        val f = fixture("cn-capture.txt")
        val disks = StatsParser.parseDisks(StatsParser.section(f, "__DISK"))
        assertTrue(disks.isNotEmpty(), "the captured host must show at least one filesystem")
        assertTrue(disks.any { it.mount == "/" }, "the root filesystem must be parsed, got ${disks.map { it.mount }}")
        val root = disks.first { it.mount == "/" }
        assertTrue(root.usedPct in 0..100)
        assertTrue(root.total > 0 && root.used in 0..root.total)
        assertTrue(disks.none { it.mount == "on" }, "the df header row must not become a disk")
    }

    @Test
    fun `disk rows need six fields and a percent capacity`() {
        assertEquals(0, StatsParser.parseDisks("Filesystem 1024-blocks Used Available Capacity Mounted on").size)
        assertEquals(0, StatsParser.parseDisks("/dev/sda1 100 50 50 nope /mnt").size)
        assertEquals(0, StatsParser.parseDisks("/dev/sda1 100 50 50").size)
        // total == 0 is filtered out
        assertEquals(0, StatsParser.parseDisks("/dev/sda1 0 0 0 0% /mnt").size)
        // a normal row parses, and kB become bytes
        val one = StatsParser.parseDisks("/dev/sda1 2048 1024 1024 50% /mnt")
        assertEquals(1, one.size)
        assertEquals(2048L * 1024L, one[0].total)
        assertEquals("/mnt", one[0].mount)
    }

    @Test
    fun `a mount point containing a space is truncated at the space`() {
        // Documents original behaviour: the parser splits on whitespace, so p[5] is only the
        // first word of the mount point. Kept visible rather than silently "fixed".
        val d = StatsParser.parseDisks("/dev/sdb1 4096 2048 2048 50% /media/My Disk")
        assertEquals(1, d.size)
        assertEquals("/media/My", d[0].mount)
    }

    // ---------- systemd ----------

    @Test
    fun `services parse from the real captured systemctl output`() {
        val f = fixture("cn-services.txt")
        val idx = f.indexOf("__FAILED")
        assertTrue(idx > 0, "the services fixture must carry the __FAILED marker")
        val services = StatsParser.parseServices(f.substring(0, idx))
        assertTrue(services.isNotEmpty(), "the captured host runs services")
        assertTrue(services.all { it.unit.isNotBlank() }, "no service may have a blank unit name")
        assertTrue(services.any { it.unit.endsWith(".service") })
    }

    @Test
    fun `failed unit counting needs the dot service marker`() {
        val v = "a.service loaded failed failed A\nb.timer loaded active active B\nc.service loaded failed failed C"
        assertEquals(2, StatsParser.countFailed(v))
        assertEquals(0, StatsParser.countFailed(""))
        assertEquals(0, StatsParser.countFailed("nothing failed here"))
        // and against the real host capture
        val f = fixture("cn-services.txt")
        val failedPart = f.substringAfter("__FAILED")
        val n = StatsParser.countFailed(failedPart)
        assertTrue(n >= 0)
        assertEquals(failedPart.lines().count { it.contains(".service") }, n)
    }

    // ---------- whole pipeline ----------

    @Test
    fun `parseAll over the real capture produces a coherent snapshot`() {
        val s = StatsParser.parseAll(fixture("cn-capture.txt"))
        assertTrue(s.cpuPct in 0f..100f, "cpuPct out of range: ${s.cpuPct}")
        assertTrue(s.memTotal > 0, "memTotal must be known")
        assertTrue(s.memUsed in 0..s.memTotal, "memUsed must be within memTotal")
        assertTrue(s.memUsedPct in 0f..100f, "memUsedPct out of range: ${s.memUsedPct}")
        assertTrue(s.disks.isNotEmpty())
        assertTrue(s.hostname.isNotBlank(), "hostname must be captured")
        assertTrue(s.uptime.isNotBlank(), "uptime must be captured")
    }

    @Test
    fun `parseAll on empty input degrades to zeroes instead of throwing`() {
        val s = StatsParser.parseAll("")
        assertEquals(0f, s.cpuPct)
        assertEquals(0L, s.memTotal)
        assertEquals(0, s.disks.size)
        assertEquals("", s.hostname)
    }

    // ---------- MAC ----------

    @Test
    fun `mac shape test accepts real macs and rejects lookalikes`() {
        assertTrue(StatsParser.isMac("b0:41:6f:15:4d:8a"))
        assertTrue(StatsParser.isMac("B0:41:6F:15:4D:8A"))
        assertFalse(StatsParser.isMac("b0:41:6f:15:4d"))
        assertFalse(StatsParser.isMac("b0-41-6f-15-4d-8a"))
        assertFalse(StatsParser.isMac(""))
    }
}
