import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'color_schemes.dart';

class ThemeSettings {
  final ThemeMode themeMode;
  final ColorPalette colorPalette;

  ThemeSettings({
    this.themeMode = ThemeMode.system,
    this.colorPalette = ColorPalette.defaultPalette,
  });

  ThemeSettings copyWith({
    ThemeMode? themeMode,
    ColorPalette? colorPalette,
  }) {
    return ThemeSettings(
      themeMode: themeMode ?? this.themeMode,
      colorPalette: colorPalette ?? this.colorPalette,
    );
  }
}

class ThemeNotifier extends StateNotifier<ThemeSettings> {
  ThemeNotifier() : super(ThemeSettings());

  void setThemeMode(ThemeMode mode) {
    state = state.copyWith(themeMode: mode);
  }

  void setColorPalette(ColorPalette palette) {
    state = state.copyWith(colorPalette: palette);
  }

  void toggleTheme() {
    if (state.themeMode == ThemeMode.light) {
      state = state.copyWith(themeMode: ThemeMode.dark);
    } else {
      state = state.copyWith(themeMode: ThemeMode.light);
    }
  }
}

final themeProvider = StateNotifierProvider<ThemeNotifier, ThemeSettings>((ref) {
  return ThemeNotifier();
});
