import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/network/api_client.dart';
import 'core/theme/app_theme.dart';
import 'core/theme/theme_provider.dart';
import 'core/router/app_router.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiConfig.initialize();
  unawaited(ApiConfig.autoSelectReachableBaseUrl());

  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    final themeSettings = ref.watch(themeProvider);
    

    return MaterialApp.router(
      title: 'FoodLens',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(palette: themeSettings.colorPalette),
      darkTheme: AppTheme.dark(palette: themeSettings.colorPalette),
      themeMode: themeSettings.themeMode,
      routerConfig: router,
    );
  }
}
