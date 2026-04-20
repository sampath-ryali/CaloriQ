import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../shared/health_stats.dart';

class HealthNotifier extends StateNotifier<HealthStats> {
  HealthNotifier() : super(HealthStats.empty());

  void updateWeight(double weight) {
    state = state.copyWith(weight: weight);
  }

  void updateHeight(double height) {
    state = state.copyWith(height: height);
  }

  void updateBodyType(BodyType bodyType) {
    state = state.copyWith(bodyType: bodyType);
  }

  void addAllergy(String allergy) {
    if (!state.allergies.contains(allergy)) {
      state = state.copyWith(allergies: [...state.allergies, allergy]);
    }
  }

  void removeAllergy(String allergy) {
    state = state.copyWith(
      allergies: state.allergies.where((a) => a != allergy).toList(),
    );
  }
}

final healthProvider = StateNotifierProvider<HealthNotifier, HealthStats>((ref) {
  return HealthNotifier();
});
