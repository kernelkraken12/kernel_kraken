# TuxDeck — unit-test environment.
#
# TuxDeck's shipped artifact is an Android APK, but its TESTABLE logic (the /proc, df, systemd and
# Wake-on-LAN parsing) is deliberately pure Kotlin with no Android imports, so it runs on a plain
# JVM. That is what this image does: fetch a JDK + the Kotlin compiler + the JUnit console, compile,
# and run the suite. No Android SDK required.
#
#   docker build -t tuxdeck-tests .
#   docker run --rm tuxdeck-tests
#
# Expected tail:  [ 23 tests successful ]  [ 0 tests failed ]
#
# NOTE (measured, 2026-10-06): the Kotlin stdlib must be on BOTH classpaths or every test fails with
# NoClassDefFoundError kotlin/text/Regex. That is why STDLIB appears twice below.

FROM eclipse-temurin:21-jdk

ARG KOTLIN_VERSION=2.4.20
ARG JUNIT_VERSION=1.10.2

WORKDIR /opt
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip \
 && rm -rf /var/lib/apt/lists/* \
 && curl -sL "https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip" -o k.zip \
 && unzip -q k.zip && rm k.zip && chmod +x /opt/kotlinc/bin/* \
 && curl -sL "https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/${JUNIT_VERSION}/junit-platform-console-standalone-${JUNIT_VERSION}.jar" \
      -o /opt/junit-console.jar

WORKDIR /work
COPY src/ /work/src/

RUN set -eux; \
    kotlinc -J-Xmx1200m -cp /opt/junit-console.jar -d /work/build-out \
      $(find /work/src/main/kotlin -name '*.kt') \
      $(find /work/src/test/kotlin -name '*.kt')

CMD ["sh", "-c", "java -cp /opt/junit-console.jar:/opt/kotlinc/lib/kotlin-stdlib.jar org.junit.platform.console.ConsoleLauncher execute --class-path /work/build-out:/work/src/test/resources:/opt/kotlinc/lib/kotlin-stdlib.jar --scan-class-path /work/build-out --details=tree --disable-ansi-colors"]
