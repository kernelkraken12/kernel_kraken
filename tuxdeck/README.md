# 🐧⚡ TuxDeck

**Mission control for your Linux fleet, in your pocket** — an Android cockpit for any SSH-able
machine: live CPU/MEM/load, systemd unit state, the journal, a real PTY terminal, and a big glowing
power button with Wake-on-LAN.

> **Primary repository:** [kernel_kraken](https://github.com/kernelkraken12/kernel_kraken) · This
> project was built with AI assistance.

*"roads? where we're going, we don't need roads."*

---

## What problem does this solve?

Your Linux box is in another room, and you want to know whether it is healthy, what systemd is
unhappy about, and to reboot it — without opening a laptop or hunting for a keyboard. TuxDeck puts
that on your phone: it SSHes to the machine you already own and shows you its real state, read from
`/proc`, `systemctl` and `journalctl` on the host itself. No agent to install on the server, no
account, no cloud, no telemetry.

## Features

- **Live stats strip** — CPU, memory and 1-minute load as an always-visible row, refreshed every 3 s
  over a **single** SSH round trip (two `/proc/stat` samples, `/proc/meminfo`, `/proc/loadavg`,
  `uptime -p`, `hostname`, `df -P` — all parsed on-device).
- **Overview** — gauge rings, a sparkline of CPU history, system card, per-mount disk bars.
- **Hero power button** — tap to send a **Wake-on-LAN** magic packet when the machine is off;
  suspend / reboot / poweroff / lock behind confirmations when it is on.
- **Services** — `systemctl list-units` with state colours and a failed-unit counter.
- **Journal** — `journalctl -n 120` on demand, selectable text.
- **Terminal** — a real interactive PTY shell (`xterm-256color`), not a command runner.

## Quick start

```bash
git clone https://github.com/kernelkraken12/kernel_kraken
cd kernel_kraken/tuxdeck/android
./gradlew assembleDebug          # needs an Android SDK + JDK 17 or newer
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Then in the app: **Add host** → hostname/IP, port 22, user, and either a password or an OpenSSH
private key. Tap the host to connect.

Host-side prerequisites on the machine you connect *to*:

- `sshd` running (any Linux with OpenSSH works)
- optional: `ethtool` + the `tuxdeck-wol.service` unit in `systemd/` so the power button can wake it

## How it works

```
phone ──SSH (sshj)──▶ your Linux host
                       ├─ grep ^cpu /proc/stat          ─┐
                       ├─ grep MemTotal /proc/meminfo    │ one round trip,
                       ├─ cat /proc/loadavg              │ parsed on-device
                       ├─ uptime -p; hostname            │
                       └─ df -P -x tmpfs …              ─┘
```

Every parser lives in `src/main/kotlin/tuxdeck/sys/StatsParser.kt` as a **pure function** — String in,
data out. No Android, no sshj, no coroutines. That is deliberate: it is what makes the logic testable
on a plain JVM, and it is where the project's tests live.

## Layout

```
tuxdeck/
├── src/main/kotlin/tuxdeck/sys/StatsParser.kt   ← pure parsing (tested)
├── src/main/kotlin/tuxdeck/sys/WolPacket.kt     ← magic-packet build (tested)
├── src/test/kotlin/tuxdeck/sys/*.kt             ← 23 JUnit tests
├── src/test/resources/cn-capture.txt            ← REAL host capture used as the fixture
├── src/test/resources/cn-services.txt           ← REAL systemctl capture
├── android/                                     ← the Android app (Gradle project) + INTEGRATION.md
├── systemd/tuxdeck-wol.service                  ← optional host-side WoL unit
├── examples/                                    ← sample host config + WoL env
├── Dockerfile                                   ← runs the test suite, no Android SDK needed
├── PROOF-OF-RUN.txt                             ← the exact commands and their measured result
└── CHECKLIST.md                                 ← security review, edge cases, open items
```

## Development and tests

The unit tests need only a **JDK, the Kotlin compiler and the JUnit console** — deliberately no
Android SDK, because the tested code has no Android imports.

```bash
# 1. toolchain (no root needed — these are plain archives)
export JAVA_HOME=/path/to/jdk-21
export PATH="$JAVA_HOME/bin:/path/to/kotlinc/bin:$PATH"
STDLIB=/path/to/kotlinc/lib/kotlin-stdlib.jar
JUNIT=junit-platform-console-standalone-1.10.2.jar

# 2. compile the core and the tests
kotlinc -J-Xmx1200m -cp "$JUNIT" -d build-out \
  src/main/kotlin/tuxdeck/sys/*.kt src/test/kotlin/tuxdeck/sys/*.kt

# 3. run them — the Kotlin stdlib must be on BOTH classpaths
java -cp "$JUNIT:$STDLIB" org.junit.platform.console.ConsoleLauncher execute \
  --class-path "build-out:src/test/resources:$STDLIB" \
  --scan-class-path build-out --details=tree
```

Expected tail:

```
[        23 tests found           ]
[        23 tests successful      ]
[         0 tests failed          ]
```

⚠ **The stdlib trap, measured 2026-10-06:** with `kotlin-stdlib.jar` missing from the runtime
classpath, all 23 tests fail with `NoClassDefFoundError: kotlin/text/Regex`. kotlinc compiles
*against* the stdlib but does not bundle it. That is why the jar appears twice above.

Or just use Docker, which does all of the above for you:

```bash
docker build -t tuxdeck-tests . && docker run --rm tuxdeck-tests
```

## Security notes — read these

TuxDeck holds SSH credentials on a phone, so the honest list matters more than the feature list:

1. **Host keys are not verified.** `ssh/Ssh.kt` registers a `HostKeyVerifier` that returns `true` for
   every key, so a man-in-the-middle on the network path is not detected. The code comments call this
   "TOFU-lite", but nothing is actually persisted, so it is not trust-on-first-use — it is
   trust-on-every-use. **Fix direction:** pin the key on first connect, store the fingerprint, and
   warn loudly on change.
2. **Credentials are stored in plain text** in the app-private `hosts.json` (`filesDir`). App-private
   is not the same as encrypted — on a rooted or backed-up device the file is readable. **Fix
   direction:** Android Keystore-backed encryption.
3. **A signing keystore must never be committed.** See CHECKLIST.md — `.gitignore` is hardened for
   this and there is a pre-push check.
4. Wake-on-LAN broadcasts to `255.255.255.255` only. On a routed network you need a **directed**
   broadcast (`x.x.x.255` for the target's subnet).

## License

MIT — see [LICENSE](LICENSE). The heavy lifting is done by external libraries invoked as
dependencies (`sshj`, BouncyCastle), which keep their own licenses.
