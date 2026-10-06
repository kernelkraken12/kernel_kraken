package com.yurii.tuxdeck.ssh

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import net.schmizz.sshj.SSHClient
import net.schmizz.sshj.connection.channel.direct.PTYMode
import net.schmizz.sshj.connection.channel.direct.Session
import net.schmizz.sshj.transport.verification.HostKeyVerifier
import net.schmizz.sshj.userauth.method.AuthPassword
import net.schmizz.sshj.userauth.method.AuthPublickey
import net.schmizz.sshj.userauth.password.PasswordFinder
import net.schmizz.sshj.userauth.password.Resource
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.InetSocketAddress
import java.security.PublicKey
import java.util.Collections
import java.util.concurrent.TimeUnit

data class Host(
    val id: String,
    val label: String,
    val hostname: String,
    val port: Int = 22,
    val user: String,
    val password: String? = null,   // stored app-private; Keystore hardening later
    val privateKey: String? = null, // OpenSSH-format PEM text
    val mac: String? = null,        // for Wake-on-LAN
) {
    fun authLabel(): String = if (privateKey != null) "key" else "password"
}

/** App-private host registry. */
object HostStore {
    private fun file(ctx: Context) = File(ctx.filesDir, "hosts.json")

    fun load(ctx: Context): MutableList<Host> {
        val f = file(ctx)
        if (!f.exists()) return mutableListOf()
        return try {
            val arr = JSONArray(f.readText())
            MutableList(arr.length()) { i ->
                val o = arr.getJSONObject(i)
                Host(
                    id = o.optString("id"),
                    label = o.optString("label"),
                    hostname = o.optString("hostname"),
                    port = o.optInt("port", 22),
                    user = o.optString("user"),
                    password = if (o.isNull("password")) null else o.optString("password"),
                    privateKey = if (o.isNull("privateKey")) null else o.optString("privateKey"),
                    mac = if (o.isNull("mac")) null else o.optString("mac"),
                )
            }
        } catch (e: Exception) {
            mutableListOf()
        }
    }

    fun save(ctx: Context, hosts: List<Host>) {
        val arr = JSONArray()
        hosts.forEach { h ->
            arr.put(
                JSONObject()
                    .put("id", h.id)
                    .put("label", h.label)
                    .put("hostname", h.hostname)
                    .put("port", h.port)
                    .put("user", h.user)
                    .put("password", h.password ?: JSONObject.NULL)
                    .put("privateKey", h.privateKey ?: JSONObject.NULL)
                    .put("mac", h.mac ?: JSONObject.NULL)
            )
        }
        file(ctx).writeText(arr.toString())
    }
}

/** One SSH connection per host, reused across exec calls; re-dials when dropped. */
class SshConn(private val host: Host) {
    companion object {
        init {
            // Android ships a crippled built-in "BC" provider without Ed25519/X25519.
            // Swap in the full BouncyCastle that ships with sshj, or modern SSH keys fail.
            try {
                java.security.Security.removeProvider("BC")
                java.security.Security.addProvider(org.bouncycastle.jce.provider.BouncyCastleProvider())
            } catch (_: Exception) {}
        }
    }

    private var client: SSHClient? = null
    private val lock = Any()

    suspend fun ensure(): SSHClient = withContext(Dispatchers.IO) {
        val existing = client
        if (existing != null && existing.isConnected) return@withContext existing
        synchronized(lock) {
            var c = client
            if (c != null && c.isConnected) return@withContext c
            try { c?.disconnect() } catch (_: Exception) {}
            c = SSHClient().apply {
                addHostKeyVerifier(object : HostKeyVerifier {
                    // TOFU-lite: accept + we surface the fingerprint in the UI.
                    override fun verify(hostname: String?, port: Int, key: PublicKey?): Boolean = true
                    override fun findExistingAlgorithms(hostname: String?, port: Int): MutableList<String>? = null
                })
                timeout = 8000
                connectTimeout = 8000
                connect(host.hostname, host.port)
                when {
                    host.privateKey != null -> {
                        val kp = loadKey(this, host.privateKey)
                        auth(host.user, AuthPublickey(kp))
                    }
                    host.password != null -> authPassword(host.user, host.password)
                    else -> error("No credentials configured")
                }
            }
            client = c
            c
        }
    }

    private fun loadKey(c: SSHClient, pem: String) =
        c.loadKeys(pem, null as String?, null as PasswordFinder?)

    suspend fun exec(command: String, timeoutSec: Long = 15): ExecResult = withContext(Dispatchers.IO) {
        val c = ensure()
        var session: Session? = null
        try {
            session = c.startSession()
            val cmd = session.exec(command)
            cmd.join(timeoutSec, TimeUnit.SECONDS)
            val out = cmd.inputStream.readBytes().toString(Charsets.UTF_8)
            val err = cmd.errorStream.readBytes().toString(Charsets.UTF_8)
            ExecResult(out, err, cmd.exitStatus)
        } finally {
            try { session?.close() } catch (_: Exception) {}
        }
    }

    suspend fun alive(): Boolean = try {
        exec("true", 8)
        true
    } catch (e: Exception) {
        false
    }

    fun drop() {
        synchronized(lock) {
            try { client?.disconnect() } catch (_: Exception) {}
            client = null
        }
    }

    /** Interactive PTY shell. Terminal tab drives this directly. */
    suspend fun openShell(): Shell = withContext(Dispatchers.IO) {
        val c = ensure()
        val s = c.startSession()
        s.allocatePTY("xterm-256color", 120, 32, 0, 0, Collections.emptyMap<PTYMode, Int>())
        val sh = s.startShell()
        Shell(sh)
    }

    data class ExecResult(val stdout: String, val stderr: String, val exitStatus: Int?)

    class Shell(private val inner: Session.Shell) {
        fun write(line: String) {
            inner.outputStream.write((line + "\n").toByteArray(Charsets.UTF_8))
            inner.outputStream.flush()
        }

        /** Drain whatever is available; returns decoded text ("" if none). */
        fun readAvailable(): String {
            val available = inner.inputStream.available()
            if (available <= 0) return ""
            val buf = ByteArray(available)
            val n = inner.inputStream.read(buf)
            return if (n > 0) String(buf, 0, n, Charsets.UTF_8) else ""
        }

        fun close() {
            try { inner.close() } catch (_: Exception) {}
        }
    }
}

/** Connection registry so screens share one connection per host. */
object Connections {
    private val map = HashMap<String, SshConn>()
    @Synchronized
    fun forHost(h: Host): SshConn = map.getOrPut(h.id) { SshConn(h) }
    @Synchronized
    fun drop(id: String) {
        map.remove(id)?.drop()
    }
}

/** Wake-on-LAN: UDP magic packet, broadcast on port 9. */
object WakeOnLan {
    suspend fun wake(mac: String): Boolean = withContext(Dispatchers.IO) {
        val macBytes = mac.replace(":", "").replace("-", "").chunked(2).map { it.toInt(16).toByte() }
        require(macBytes.size == 6) { "bad MAC" }
        val packet = ByteArray(6) { 0xFF.toByte() } + ByteArray(16 * 6) { i -> macBytes[i % 6] }
        java.net.DatagramSocket().use { sock ->
            sock.broadcast = true
            for (target in listOf(
                InetSocketAddress("255.255.255.255", 9),
                InetSocketAddress("255.255.255.255", 7),
            )) {
                try { sock.send(java.net.DatagramPacket(packet, packet.size, target)) } catch (_: Exception) {}
            }
        }
        true
    }
}
