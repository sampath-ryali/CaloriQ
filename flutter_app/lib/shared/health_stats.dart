enum BodyType {
  lean,
  fit,
  fitBulky,
  overweight,
}

extension BodyTypeExtension on BodyType {
  String get displayName {
    switch (this) {
      case BodyType.lean:
        return 'Lean';
      case BodyType.fit:
        return 'Fit';
      case BodyType.fitBulky:
        return 'Fit-Bulky';
      case BodyType.overweight:
        return 'Overweight';
    }
  }
}

class HealthStats {
  final double? weight;
  final double? height;
  final BodyType? bodyType;
  final List<String> allergies;

  HealthStats({
    this.weight,
    this.height,
    this.bodyType,
    this.allergies = const [],
  });

  double? get bmi {
    if (weight == null || height == null || height == 0) return null;
    return weight! / ((height! / 100) * (height! / 100));
  }

  String get bmiCategory {
    final bmiValue = bmi;
    if (bmiValue == null) return 'Unknown';
    if (bmiValue < 18.5) return 'Underweight';
    if (bmiValue < 25) return 'Normal';
    if (bmiValue < 30) return 'Overweight';
    return 'Obese';
  }

  HealthStats copyWith({
    double? weight,
    double? height,
    BodyType? bodyType,
    List<String>? allergies,
  }) {
    return HealthStats(
      weight: weight ?? this.weight,
      height: height ?? this.height,
      bodyType: bodyType ?? this.bodyType,
      allergies: allergies ?? this.allergies,
    );
  }

  factory HealthStats.empty() {
    return HealthStats();
  }
}
