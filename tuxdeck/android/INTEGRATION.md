# Wiring the app to the tested core (NOT YET APPLIED)

TuxDeck's parsing logic lived inline inside `fetchStats(conn)` in
`sys/Stats.kt`, which is why the project could ship with no tests: there was nothing callable to
test. `../src/main/kotlin/tuxdeck/sys/StatsParser.kt` and `WolPacket.kt` are that same logic
extracted into pure functions — **and those are covered by 23 passing tests**.

The app in this directory is **unmodified**. It is deliberately not rewired, because rewiring it
requires compiling an Android app, and the seat that prepared this tree has **no Android SDK**
(measured: no java/kotlinc/gradle/docker). Shipping a code change that was never compiled would
violate rule #8 — TESTED — so the change is documented here instead of silently applied.

## The change, when someone with the SDK can compile it

1. Add the shared source directory to `app/build.gradle.kts`:

```kotlin
android {
    sourceSets["main"].java.srcDirs("../../src/main/kotlin")
}
```

2. In `sys/Stats.kt`, delete the inline parsing and delegate:

```kotlin
suspend fun fetchStats(conn: SshConn): Stats = withContext(Dispatchers.IO) {
    val script = /* unchanged */
    StatsParser.parseAll(conn.exec(script, 15).stdout)
}
```

3. In `sys/Stats.kt`'s service journal and MAC helpers, call
   `StatsParser.parseServices` / `StatsParser.countFailed` / `StatsParser.isMac`.

4. In `ssh/Ssh.kt`, replace the inline packet construction in `WakeOnLan.wake` with
   `WolPacket.buildMagicPacket(mac) ?: return false`, so a malformed MAC shows an error instead of
   throwing out of a UI path.

5. `./gradlew test` must run the same 23 tests inside the Android build. **Until that is done, the
   Android module has no test coverage and this file is the only record of it.**

## What the extraction changes (declared)

Two behaviour changes, both covered by tests, both listed in CHECKLIST.md:
guest/guest_nice are excluded from the CPU total, and a malformed MAC returns null instead of throwing.
