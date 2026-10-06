package com.yurii.tuxdeck.ui

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// DeLorean × phosphor terminal palette:
// stainless steel panels, time-circuits LED red, flux blue, terminal green.
val Bg = Color(0xFF05070C)
val Panel = Color(0xFF0C0F16)
val PanelHi = Color(0xFF141926)
val Green = Color(0xFF00E887)
val Amber = Color(0xFFFFB454)
val Red = Color(0xFFFF5C5C)
val Ink = Color(0xFFE2EAF5)
val InkLo = Color(0xFF7C8AA0)
val Grid = Color(0xFF1B2330)
val Steel = Color(0xFFB8BEC8)       // brushed stainless
val SteelDim = Color(0xFF3A4148)
val FluxBlue = Color(0xFF37C8FF)    // flux capacitor glow
val LedRed = Color(0xFFFF3B30)      // time-circuits LED
val LedAmber = Color(0xFFFFB454)

val Mono = FontFamily.Monospace

private val DeckScheme = darkColorScheme(
    primary = Green,
    onPrimary = Color(0xFF04120B),
    secondary = Amber,
    onSecondary = Color(0xFF1A1206),
    tertiary = Color(0xFF7DF9FF),
    background = Bg,
    onBackground = Ink,
    surface = Panel,
    onSurface = Ink,
    surfaceVariant = PanelHi,
    onSurfaceVariant = InkLo,
    error = Red,
    outline = Grid,
)

private val DeckType = Typography(
    headlineMedium = TextStyle(fontFamily = Mono, fontWeight = FontWeight.Bold, letterSpacing = (-0.5).sp),
    titleLarge = TextStyle(fontFamily = Mono, fontWeight = FontWeight.Bold),
    titleMedium = TextStyle(fontFamily = Mono, fontWeight = FontWeight.SemiBold),
    bodyLarge = TextStyle(fontFamily = Mono),
    bodyMedium = TextStyle(fontFamily = Mono),
    bodySmall = TextStyle(fontFamily = Mono),
    labelLarge = TextStyle(fontFamily = Mono, fontWeight = FontWeight.SemiBold, letterSpacing = 0.4.sp),
    labelMedium = TextStyle(fontFamily = Mono),
    labelSmall = TextStyle(fontFamily = Mono, fontWeight = FontWeight.Medium, letterSpacing = 0.4.sp, fontSize = 11.sp),
)

@Composable
fun DeckTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = DeckScheme, typography = DeckType, content = content)
}

/** Panel with a terminal-style frame: thin green border + corner accents. */
@Composable
fun TermCard(
    title: String? = null,
    modifier: Modifier = Modifier,
    accent: Color = Steel,
    content: @Composable () -> Unit,
) {
    Box(
        modifier = modifier
            .background(Panel, RoundedCornerShape(10.dp))
            .border(1.dp, accent.copy(alpha = 0.45f), RoundedCornerShape(10.dp))
            .drawBehind {
                val l = 10.dp.toPx()
                val s = 2.dp.toPx()
                // corner accents
                drawLine(accent, Offset(0f, 0f), Offset(l, 0f), s)
                drawLine(accent, Offset(0f, 0f), Offset(0f, l), s)
                drawLine(accent, Offset(size.width, 0f), Offset(size.width - l, 0f), s)
                drawLine(accent, Offset(size.width, 0f), Offset(size.width, l), s)
            }
    ) {
        if (title != null) {
            Box(
                Modifier
                    .background(PanelHi)
                    .padding(horizontal = 10.dp, vertical = 3.dp)
            ) {
                androidx.compose.material3.Text(
                    title,
                    style = MaterialTheme.typography.labelSmall,
                    color = accent,
                )
            }
        }
        content()
    }
}

/** Round progress gauge. */
@Composable
fun GaugeRing(
    fraction: Float,
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    color: Color = Green,
) {
    Canvas(modifier = modifier) {
        val stroke = 7.dp.toPx()
        val inset = stroke / 2
        val arc = size.minDimension - inset * 2
        drawArc(
            color = Grid,
            startAngle = -90f, sweepAngle = 360f, useCenter = false,
            topLeft = Offset(inset, inset),
            size = androidx.compose.ui.geometry.Size(arc, arc),
            style = Stroke(stroke, cap = StrokeCap.Round),
        )
        drawArc(
            color = color,
            startAngle = -90f, sweepAngle = 360f * fraction.coerceIn(0f, 1f), useCenter = false,
            topLeft = Offset(inset, inset),
            size = androidx.compose.ui.geometry.Size(arc, arc),
            style = Stroke(stroke, cap = StrokeCap.Round),
        )
    }
    // label/value drawn by caller overlay for layout freedom
}

/** Braille sparkline: one character per sample, the funkier the better. */
fun brailleSpark(samples: List<Float>, width: Int = 40): String {
    if (samples.isEmpty()) return "▁▁▁"
    val chars = " ⣀⣄⣤⣦⣶⣷⣿"
    val recent = samples.takeLast(width)
    return recent.joinToString("") { v ->
        val idx = ((v.coerceIn(0f, 100f) / 100f) * (chars.length - 1)).toInt()
            .coerceIn(0, chars.length - 1)
        chars[idx].toString()
    }
}

/** Time-circuits LED readout: label + glowing red value, DeLorean dash style. */
@Composable
fun LedReadout(label: String, value: String, modifier: Modifier = Modifier) {
    androidx.compose.foundation.layout.Column(modifier) {
        androidx.compose.material3.Text(
            label,
            style = MaterialTheme.typography.labelSmall,
            color = InkLo,
        )
        androidx.compose.material3.Text(
            value,
            style = MaterialTheme.typography.titleLarge.copy(
                fontSize = 22.sp,
                letterSpacing = 2.sp,
                fontWeight = FontWeight.Bold,
            ),
            color = LedRed,
            modifier = Modifier.drawBehind {
                // LED glow
                drawRect(LedRed.copy(alpha = 0.18f))
            },
        )
    }
}

/** Flux capacitor: three pulsing dots in a Y. Purely ceremonial. */
@Composable
fun FluxCapacitor(modifier: Modifier = Modifier) {
    val transition = androidx.compose.animation.core.rememberInfiniteTransition(label = "flux")
    val pulse by transition.animateFloat(
        initialValue = 0.25f,
        targetValue = 1f,
        animationSpec = androidx.compose.animation.core.infiniteRepeatable(
            androidx.compose.animation.core.tween(900),
            androidx.compose.animation.core.RepeatMode.Reverse,
        ),
        label = "pulse",
    )
    Canvas(modifier = modifier) {
        val w = size.width
        val h = size.height
        fun glow(c: Offset, r: Float) {
            drawCircle(FluxBlue.copy(alpha = 0.18f * pulse), r * 2.2f, c)
            drawCircle(FluxBlue.copy(alpha = pulse), r, c)
        }
        // Y shape: top-left, top-right, bottom center feeding middle
        val topL = Offset(w * 0.22f, h * 0.18f)
        val topR = Offset(w * 0.78f, h * 0.18f)
        val mid = Offset(w * 0.5f, h * 0.55f)
        val bot = Offset(w * 0.5f, h * 0.85f)
        val r = w * 0.09f
        listOf(topL, topR, bot).forEach { glow(it, r) }
        glow(mid, r * 1.25f)
    }
}

/** Blinking terminal cursor. */
@Composable
fun BlinkCursor(modifier: Modifier = Modifier, color: Color = Green) {
    val transition = androidx.compose.animation.core.rememberInfiniteTransition(label = "cursor")
    val alpha by transition.animateFloat(
        initialValue = 1f,
        targetValue = 0.15f,
        animationSpec = androidx.compose.animation.core.infiniteRepeatable(
            androidx.compose.animation.core.tween(600),
            androidx.compose.animation.core.RepeatMode.Reverse,
        ),
        label = "blink",
    )
    Canvas(modifier = modifier) {
        drawRect(color = color.copy(alpha = alpha))
    }
}

fun fmtBytes(n: Long): String = when {
    n < 1024 -> "$n B"
    n < 1024 * 1024 -> "%.1f KB".format(n / 1024f)
    n < 1024L * 1024 * 1024 -> "%.1f MB".format(n / 1024f / 1024f)
    else -> "%.1f GB".format(n / 1024f / 1024f / 1024f)
}

val ASCII_TUX = """
      _____
     /     \
    | () () |
     \  ^  /
      |||||
      |||||
""".trimIndent()
