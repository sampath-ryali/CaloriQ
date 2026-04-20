import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'health_provider.dart';
import '../../shared/health_stats.dart';

class HealthStatsScreen extends ConsumerStatefulWidget {
  const HealthStatsScreen({super.key});

  @override
  ConsumerState<HealthStatsScreen> createState() => _HealthStatsScreenState();
}

class _HealthStatsScreenState extends ConsumerState<HealthStatsScreen> {
  final _weightController = TextEditingController();
  final _heightController = TextEditingController();
  final List<String> _commonAllergies = [
    'Dairy',
    'Eggs',
    'Peanuts',
    'Tree nuts',
    'Fish',
    'Shellfish',
    'Soy',
    'Wheat/Gluten',
  ];

  @override
  void dispose() {
    _weightController.dispose();
    _heightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final healthStats = ref.watch(healthProvider);

    _weightController.text = healthStats.weight?.toString() ?? '';
    _heightController.text = healthStats.height?.toString() ?? '';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Health Stats'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Body Metrics',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),

            // Weight
            TextField(
              controller: _weightController,
              decoration: const InputDecoration(
                labelText: 'Weight (kg)',
                prefixIcon: Icon(Icons.monitor_weight_outlined),
              ),
              keyboardType: TextInputType.number,
              onChanged: (value) {
                final weight = double.tryParse(value);
                if (weight != null) {
                  ref.read(healthProvider.notifier).updateWeight(weight);
                }
              },
            ),
            const SizedBox(height: 16),

            // Height
            TextField(
              controller: _heightController,
              decoration: const InputDecoration(
                labelText: 'Height (cm)',
                prefixIcon: Icon(Icons.height),
              ),
              keyboardType: TextInputType.number,
              onChanged: (value) {
                final height = double.tryParse(value);
                if (height != null) {
                  ref.read(healthProvider.notifier).updateHeight(height);
                }
              },
            ),
            const SizedBox(height: 16),

            // BMI Display
            if (healthStats.bmi != null)
              Card(
                color: Theme.of(context).colorScheme.primaryContainer,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Icon(
                        Icons.analytics_outlined,
                        color: Theme.of(context).colorScheme.onPrimaryContainer,
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'BMI: ${healthStats.bmi!.toStringAsFixed(1)}',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  color: Theme.of(context).colorScheme.onPrimaryContainer,
                                ),
                          ),
                          Text(
                            healthStats.bmiCategory,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.onPrimaryContainer,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 24),

            // Body Type
            Text(
              'Body Type',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: BodyType.values.map((type) {
                final isSelected = healthStats.bodyType == type;
                return ChoiceChip(
                  label: Text(type.displayName),
                  selected: isSelected,
                  onSelected: (selected) {
                    ref.read(healthProvider.notifier).updateBodyType(type);
                  },
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            // Allergies
            Text(
              'Allergies',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: _commonAllergies.map((allergy) {
                final isSelected = healthStats.allergies.contains(allergy);
                return FilterChip(
                  label: Text(allergy),
                  selected: isSelected,
                  onSelected: (selected) {
                    if (selected) {
                      ref.read(healthProvider.notifier).addAllergy(allergy);
                    } else {
                      ref.read(healthProvider.notifier).removeAllergy(allergy);
                    }
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
}
