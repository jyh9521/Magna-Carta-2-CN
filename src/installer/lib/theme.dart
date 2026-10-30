import 'package:flutter/material.dart';

ThemeData installerTheme(Brightness brightness) {
  // Garnet, copper and parchment from the supplied logo. fromSeed supplies all
  // MD3 roles; native controls retain focus, pressed and disabled state layers.
  final colors = ColorScheme.fromSeed(
    seedColor: const Color(0xffa73c2d),
    brightness: brightness,
    secondary: brightness == Brightness.dark
        ? const Color(0xffe7bda8)
        : const Color(0xff785746),
    tertiary: brightness == Brightness.dark
        ? const Color(0xffd8c28f)
        : const Color(0xff6e5d31),
  );
  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: colors,
    fontFamily: 'Microsoft YaHei UI',
    scaffoldBackgroundColor: colors.surface,
    visualDensity: VisualDensity.standard,
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: colors.surfaceContainerLowest,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: colors.outlineVariant),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: colors.surfaceContainerLow,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      margin: EdgeInsets.zero,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(minimumSize: const Size(100, 48)),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(minimumSize: const Size(100, 48)),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    tooltipTheme: const TooltipThemeData(
      waitDuration: Duration(milliseconds: 500),
    ),
  );
}
