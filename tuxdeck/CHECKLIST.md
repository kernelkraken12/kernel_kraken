# TuxDeck — self-review checklist

Required by kernel_kraken rule #4. Everything here is either measured on 2026-10-06 or marked as an
open item. Prepared by 예지 (Yeji) on CT106.

## 1. Security notes

| # | Finding | Severity | State |
|---|---|---|---|
| 1 | `HostKeyVerifier.verify()` always returns `true` in `ssh/Ssh.kt` — host keys are never checked, so MITM is undetected. Named "TOFU-lite" in the comment but nothing is persisted → not TOFU at all. | **High** for a tool that carries credentials | **Open** — fix direction in README §Security |
| 2 | `Host.password` and `Host.privateKey` are stored as plain text in `filesDir/hosts.json`. The source comment says "Keystore hardening later". | **Medium** | **Open** |
| 3 | `hosts.json` is written with `writeText` (default perms), not created 0600. | Low | **Open** |
| 4 | The app holds `INTERNET` (required for SSH). Verify it holds no other sensitive permission at release. | Info | Verified by manifest read: `INTERNET` only |
| 5 | WO: broadcasts to `255.255.255.255` only; no directed-broadcast option. | Low | **Open** |

**Secret hygiene for this repository — the gate that matters most:**

The app's tree originally contained `keystore/`, `keystore.properties` and `local.properties`.
A signing keystore **is the app's identity**: whoever holds it can publish updates for
`com.yurii.tuxdeck` forever, and losing it means never updating that package again. `keystore.properties`
also normally carries the store and key passwords in clear.

- `.gitignore` ignores `keystore/`, `keystore.properties`, `local.properties`, `*.jks`, `*.keystore`,
  `*.p12`, `*.apk`, `*.aab`.
- The tree in this repository was assembled with those paths **excluded by name at copy time** — this
  build never touched the keystore and no passphrase was ever entered for it. Verified: a search for
  `keystore`, `keystore.properties`, `local.properties`, `*.jks`, `*.keystore` over the staged tree
  returns nothing.
- **Before any push, run:**
  ```bash
  git status --porcelain | grep -Ei 'keystore|\.jks|\.properties|\.apk' && echo 'STOP — secret staged' || echo 'clean'
  git check-ignore -v android/keystore.properties android/local.properties
  ```
- If a keystore is ever committed, rotating it is the only remedy — and the package identity is lost.

## 2. Dependencies (complete list)

Pinned by the app's `gradle/libs.versions.toml`; all are real, published artifacts:

| Dependency | Role |
|---|---|
| `androidx.core:core-ktx`, `activity-compose`, `compose-bom` + ui/foundation/material3/material-icons | Android UI (Compose) |
| `androidx.lifecycle:lifecycle-runtime-ktx` | lifecycle + coroutines |
| **`net.schmizz:sshj`** | the SSH client — the core dependency |
| `org.bouncycastle:bcprov-jdk18on`, `bcpkix-jdk18on` | SSH key algorithms Android's built-in BC provider lacks (Ed25519/X25519) |
| `org.slf4j:slf4j-nop` | silences sshj's logging |

Test-only (added by this tree): `junit-platform-console-standalone 1.10.2` (JUnit 5); the parser code
itself uses **no third-party library at all**, only the Kotlin stdlib.

## 3. Edge cases — reviewed and covered by tests

| Case | Behaviour | Test |
|---|---|---|
| `/proc/stat` line with <5 numeric fields | returns `null`, CPU% → 0f | ✓ |
| guest/guest_nice fields | **excluded** from the total (declared change) | ✓ |
| two identical samples (no clock movement) | 0f, no division by zero | ✓ |
| CPU% outside 0..100 | clamped | ✓ |
| `MemTotal`/`MemAvailable` absent | 0L, percentage guarded to 0f | ✓ |
| `df -P` header row | rejected (5th field is not a `%`) | ✓ |
| `df` row with <6 fields or a non-numeric capacity | skipped | ✓ |
| `df` row with `total == 0` | filtered out | ✓ |
| **mount point containing a space** | truncated at the space — documented, not hidden | ✓ |
| value containing `__` inside a section | truncates the section — documented | ✓ |
| `systemctl` line with <4 fields / blank unit | skipped | ✓ |
| failed-unit count | counts only lines containing `.service` | ✓ |
| MAC with hyphens or upper case | accepted | ✓ |
| **malformed MAC** | `null` (declared change — the original threw) | ✓ |
| magic packet size | exactly 102 bytes = 6×0xFF + 16×MAC | ✓ |

## 4. Declared behaviour changes vs the original app

Both are improvements, both are covered by tests, and both are visible rather than silent:

1. **CPU total excludes guest/guest_nice.** The original summed every field, but `/proc/stat` counts
   guest and guest_nice *inside* user/nice, so they were double-counted and CPU% was slightly
   inflated. Verified by mutation: restoring `p.sum()` makes the CPU test **fail**.
2. **`buildMagicPacket()` returns `null` for a malformed MAC** instead of throwing
   `NumberFormatException` out of a UI path.

The app in `android/` is **not yet rewired** to call this core — see `android/INTEGRATION.md`. It was
not rewired because the preparing seat has no Android SDK and rule #8 forbids shipping an uncompiled
change.

## 5. Exact test steps and the measured result

```bash
export JAVA_HOME=/path/to/jdk-21
export PATH="$JAVA_HOME/bin:/path/to/kotlinc/bin:$PATH"
STDLIB=/path/to/kotlinc/lib/kotlin-stdlib.jar
JUNIT=junit-platform-console-standalone-1.10.2.jar

kotlinc -J-Xmx1200m -cp "$JUNIT" -d build-out \
  src/main/kotlin/tuxdeck/sys/*.kt src/test/kotlin/tuxdeck/sys/*.kt

java -cp "$JUNIT:$STDLIB" org.junit.platform.console.ConsoleLauncher execute \
  --class-path "build-out:src/test/resources:$STDLIB" \
  --scan-class-path build-out --details=tree
```

Measured result on CT106, 2026-10-06 (Record-Id: PROOF-OF-RUN.txt):

```
[ 23 tests found ]  [ 23 tests successful ]  [ 0 tests failed ]   — 206 ms
```

Positive controls (a suite that cannot fail is not evidence):
- stdlib absent from the runtime classpath → **23/23 FAIL** (`NoClassDefFoundError: kotlin/text/Regex`)
- `take(8).sum()` mutated back to `p.sum()` → **1 test FAILS** (the guest-exclusion test)

Toolchain used: Temurin JDK 21.0.12.1 · kotlinc 2.4.20 · junit-platform-console-standalone 1.10.2,
installed **without root** as plain archives.

## 6. Repository metadata (rule #9)

- **Description:** "Android cockpit for your Linux fleet — live CPU/mem/load, systemd units, journal and a real terminal over SSH, plus Wake-on-LAN, for any host you can ssh into."
- **Topics:** `android-opensource` · `linux` · `homelab` · `ssh` · `systemd` · `kotlin` · `foss` · `wake-on-lan` · `sysadmin` · `selfhosted`

## 7. Open items before any release

- [ ] **Confirm the LICENSE copyright holder** (`kernel_kraken contributors` was used as a safe default).
- [ ] Decide whether the release APK ships in the tree or only on GitHub Releases (currently excluded by `.gitignore`).
- [ ] Rewire `android/` to the tested core and run `./gradlew test` with the Android SDK — then the
      Android module has coverage too.
- [ ] Host-key verification (finding 1) — the top security item.
- [ ] Credential encryption (findings 2 and 3).
- [ ] Directed-broadcast Wake-on-LAN (finding 5).
- [ ] Verify on a real device before publishing: connect, stats refresh, services list, journal, PTY
      terminal, WoL power-on.

## 8. Known issues in the app that these tests do not cover

- `systemctl --failed` is capped with `| head -10`, so the failed-unit counter **undercounts above 10**
  failed units (measured: a host with more than 10 failed units reports 10).
- `parseServices` drops systemd's ACTIVE column and colours by SUB — intentional, but it means
  "active (exited)" and "active (running)" are indistinguishable in the list.
- The captured test host (cn) currently has **3 failed units** from an unrelated sync job, which is a
  real-world case the failed-unit counter was exercised against.

## 9. Canonical-structure note (declared adaptation)

kernel_kraken's canonical tree lists `src/` **and** `tests/`. This project keeps its tests in
`src/test/kotlin/` with the fixtures in `src/test/resources/`, because that is the standard JVM/Gradle
source-set layout: a Gradle Android build picks those up automatically, and the plain-kotlinc commands
in §5 work unchanged. A separate top-level `tests/` directory would have to be wired into the Android
build by hand and would break the convention every Kotlin developer expects.

This is an **adaptation, declared rather than silently dropped** — rule #7 asks for every canonical
asset, and the honest answer is that the *asset* (tests + fixtures) is present, while its *directory*
follows the language's convention. If the family prefers literal `tests/`, moving them is a two-line
change in the build files plus the paths in §5.

The same applies to `systemd/`: TuxDeck's deliverable is an Android app, so the example unit is not a
service for the app — it is the **host-side** unit (`tuxdeck-wol.service`) that enables the feature the
app's power button needs. It is a real, usable unit rather than a placeholder.
