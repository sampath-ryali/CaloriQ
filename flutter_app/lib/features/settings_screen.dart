import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/theme_provider.dart';
import '../../core/theme/color_schemes.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeSettings = ref.watch(themeProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Appearance',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 16),

          // Theme Mode
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.brightness_6),
                      const SizedBox(width: 12),
                      Text(
                        'Theme Mode',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 12,
                    children: [
                      ChoiceChip(
                        label: const Text('Light'),
                        selected: themeSettings.themeMode == ThemeMode.light,
                        onSelected: (selected) {
                          if (selected) {
                            ref.read(themeProvider.notifier).setThemeMode(ThemeMode.light);
                          }
                        },
                      ),
                      ChoiceChip(
                        label: const Text('Dark'),
                        selected: themeSettings.themeMode == ThemeMode.dark,
                        onSelected: (selected) {
                          if (selected) {
                            ref.read(themeProvider.notifier).setThemeMode(ThemeMode.dark);
                          }
                        },
                      ),
                      ChoiceChip(
                        label: const Text('System'),
                        selected: themeSettings.themeMode == ThemeMode.system,
                        onSelected: (selected) {
                          if (selected) {
                            ref.read(themeProvider.notifier).setThemeMode(ThemeMode.system);
                          }
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Color Palette
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.palette),
                      const SizedBox(width: 12),
                      Text(
                        'Color Palette',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 12,
                    children: [
                      ChoiceChip(
                        label: const Text('Default'),
                        selected: themeSettings.colorPalette == ColorPalette.defaultPalette,
                        onSelected: (selected) {
                          if (selected) {
                            ref.read(themeProvider.notifier).setColorPalette(ColorPalette.defaultPalette);
                          }
                        },
                      ),
                      ChoiceChip(
                        label: const Text('Food Theme'),
                        selected: themeSettings.colorPalette == ColorPalette.foodTheme,
                        onSelected: (selected) {
                          if (selected) {
                            ref.read(themeProvider.notifier).setColorPalette(ColorPalette.foodTheme);
                          }
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 32),

          Text(
            'About',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 16),

          Card(
            child: Column(
              children: [
                const ListTile(
                  leading: Icon(Icons.info_outline),
                  title: Text('Version'),
                  trailing: Text('1.0.0'),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.privacy_tip_outlined),
                  title: const Text('Privacy Policy'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.description_outlined),
                  title: const Text('Terms of Service'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
