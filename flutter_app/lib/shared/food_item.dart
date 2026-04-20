class FoodItem {
  final String name;
  final double calories;
  final MacroNutrients macros;
  final List<String> allergyWarnings;
  final String healthSuggestion;
  final String? imageUrl;

  FoodItem({
    required this.name,
    required this.calories,
    required this.macros,
    required this.allergyWarnings,
    required this.healthSuggestion,
    this.imageUrl,
  });

  factory FoodItem.mock() {
    return FoodItem(
      name: 'Grilled Chicken Salad',
      calories: 320,
      macros: MacroNutrients(
        protein: 35,
        carbs: 18,
        fat: 12,
      ),
      allergyWarnings: ['May contain dairy', 'Contains nuts'],
      healthSuggestion:
          'Great choice! This meal is high in protein and low in carbs, perfect for muscle building and weight management.',
    );
  }

  factory FoodItem.fromImage(String imagePath) {
    final mockFoods = [
      FoodItem(
        name: 'Avocado Toast',
        calories: 280,
        macros: MacroNutrients(protein: 8, carbs: 32, fat: 16),
        allergyWarnings: ['Contains gluten'],
        healthSuggestion:
            'Healthy fats from avocado! Consider adding protein for a balanced meal.',
      ),
      FoodItem(
        name: 'Grilled Salmon',
        calories: 420,
        macros: MacroNutrients(protein: 48, carbs: 0, fat: 24),
        allergyWarnings: ['Fish/seafood'],
        healthSuggestion:
            'Excellent omega-3 source! Perfect for heart health and brain function.',
      ),
      FoodItem(
        name: 'Chocolate Cake',
        calories: 580,
        macros: MacroNutrients(protein: 6, carbs: 72, fat: 28),
        allergyWarnings: ['Contains dairy', 'Contains gluten', 'May contain eggs'],
        healthSuggestion:
            'High in sugar and calories. Enjoy in moderation as an occasional treat.',
      ),
      FoodItem(
        name: 'Greek Yogurt Bowl',
        calories: 220,
        macros: MacroNutrients(protein: 18, carbs: 24, fat: 6),
        allergyWarnings: ['Contains dairy'],
        healthSuggestion:
            'Great protein-rich breakfast! The probiotics support digestive health.',
      ),
      FoodItem(
        name: 'Quinoa Buddha Bowl',
        calories: 380,
        macros: MacroNutrients(protein: 14, carbs: 52, fat: 14),
        allergyWarnings: [],
        healthSuggestion:
            'Well-balanced plant-based meal with complete protein from quinoa.',
      ),
    ];
    
    return mockFoods[imagePath.hashCode % mockFoods.length];
  }
}

class MacroNutrients {
  final double protein;
  final double carbs;
  final double fat;

  MacroNutrients({
    required this.protein,
    required this.carbs,
    required this.fat,
  });

  double get totalCalories => (protein * 4) + (carbs * 4) + (fat * 9);
}
