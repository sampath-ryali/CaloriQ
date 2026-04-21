import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:caloriq/core/network/api_client.dart';
import '../../core/theme/theme_provider.dart';
import '../../core/theme/color_schemes.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  late final TextEditingController _baseUrlController;

  @override
  void initState() {
    super.initState();
    _baseUrlController = TextEditingController(text: ApiConfig.baseUrl);
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    super.dispose();
  }

  Future<void> _saveBaseUrl() async {
    final value = _baseUrlController.text.trim();
    final uri = Uri.tryParse(value);
    final isValid = uri != null && uri.hasScheme && uri.hasAuthority;

    if (!isValid) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a valid URL (example: http://192.168.1.10:5000/api)')),
      );
      return;
    }

    await ApiConfig.setBaseUrl(value);
    if (!mounted) {
      return;
    }

    setState(() {
      _baseUrlController.text = ApiConfig.baseUrl;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Backend URL saved: ${ApiConfig.baseUrl}')),
    );
  }

  Future<void> _resetBaseUrl() async {
    await ApiConfig.clearOverride();
    if (!mounted) {
      return;
    }

    setState(() {
      _baseUrlController.text = ApiConfig.baseUrl;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Using default URL: ${ApiConfig.defaultBaseUrl}')),
    );
  }

  @override
  Widget build(BuildContext context) {
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

          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.wifi),
                      const SizedBox(width: 12),
                      Text(
                        'Backend URL',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _baseUrlController,
                    keyboardType: TextInputType.url,
                    decoration: const InputDecoration(
                      labelText: 'API Base URL',
                      hintText: 'http://192.168.1.10:5000/api',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    ApiConfig.hasOverride
                        ? 'Custom URL active'
                        : 'Using compile-time default: ${ApiConfig.defaultBaseUrl}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      FilledButton(
                        onPressed: _saveBaseUrl,
                        child: const Text('Save URL'),
                      ),
                      const SizedBox(width: 8),
                      OutlinedButton(
                        onPressed: _resetBaseUrl,
                        child: const Text('Use Default'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
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
