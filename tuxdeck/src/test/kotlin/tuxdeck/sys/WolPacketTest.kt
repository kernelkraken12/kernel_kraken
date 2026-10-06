package tuxdeck.sys

import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class WolPacketTest {

    @Test
    fun `packet is 102 bytes - six of FF then the mac sixteen times`() {
        val mac = "b0:41:6f:15:4d:8a"
        val p = WolPacket.buildMagicPacket(mac)
        assertNotNull(p)
        assertEquals(102, p!!.size)
        assertEquals(WolPacket.PACKET_BYTES, p.size)
        for (i in 0 until 6) assertEquals(0xFF.toByte(), p[i], "byte $i must be 0xFF")
        for (r in 0 until 16) {
            for (b in 0 until 6) {
                assertEquals(
                    p[6 + b].toInt() and 0xFF,
                    p[6 + r * 6 + b].toInt() and 0xFF,
                    "repeat $r byte $b must equal the first copy",
                )
            }
        }
    }

    @Test
    fun `the mac bytes are the real values`() {
        val m = WolPacket.macToBytes("b0:41:6f:15:4d:8a")
        assertNotNull(m)
        assertArrayEquals(byteArrayOf(0xb0.toByte(), 0x41, 0x6f, 0x15, 0x4d, 0x8a.toByte()), m)
    }

    @Test
    fun `hyphens and upper case are accepted`() {
        assertArrayEquals(
            WolPacket.macToBytes("b0:41:6f:15:4d:8a"),
            WolPacket.macToBytes("B0-41-6F-15-4D-8A"),
        )
    }

    @Test
    fun `a malformed mac returns null instead of throwing`() {
        // DECLARED FIX: the original called toInt(16) and threw NumberFormatException here.
        assertNull(WolPacket.buildMagicPacket("zz:41:6f:15:4d:8a"))
        assertNull(WolPacket.buildMagicPacket("b0:41:6f:15:4d"))
        assertNull(WolPacket.buildMagicPacket("b0:41:6f:15:4d:8a:00"))
        assertNull(WolPacket.buildMagicPacket(""))
        assertNull(WolPacket.macToBytes("b0416f154d8aZZ"))
    }
}
