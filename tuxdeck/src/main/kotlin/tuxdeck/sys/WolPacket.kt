/*
 * TuxDeck — WakeOnLan magic packet, extracted from ssh/Ssh.kt so the byte layout can be tested.
 *
 * DECLARED CHANGE vs the original inline code: buildMagicPacket() returns null for a malformed MAC.
 * The original did `mac.replace(":","").chunked(2).map { it.toInt(16).toByte() }` and let
 * NumberFormatException escape into a UI path — a crash on a typo in a settings field.
 *
 * The packet itself is unchanged: 6 × 0xFF followed by the MAC repeated 16 times = 102 bytes.
 * NOTE for the CHECKLIST: sendMagicPacket() broadcasts to 255.255.255.255 only. A host on another
 * subnet, or one that ignores global broadcast, needs a DIRECTED broadcast (the subnet's own
 * x.x.x.255). This is the same limitation the family hit with its own PC's Wake-on-LAN.
 */
package tuxdeck.sys

object WolPacket {

    const val PACKET_BYTES = 102      // 6 + 16×6
    const val REPEATS = 16

    /** "aa:bb:cc:dd:ee:ff" / "AA-BB-CC-DD-EE-FF" → 6 bytes. null when it is not a MAC. */
    fun macToBytes(mac: String): ByteArray? {
        val hex = mac.replace(":", "").replace("-", "")
        if (hex.length != 12) return null
        val out = ByteArray(6)
        for (i in 0 until 6) {
            val v = hex.substring(i * 2, i * 2 + 2).toIntOrNull(16) ?: return null
            out[i] = v.toByte()
        }
        return out
    }

    /** The 102-byte magic packet, or null if the MAC is malformed. */
    fun buildMagicPacket(mac: String): ByteArray? {
        val m = macToBytes(mac) ?: return null
        return ByteArray(6) { 0xFF.toByte() } + ByteArray(REPEATS * 6) { i -> m[i % 6] }
    }
}
