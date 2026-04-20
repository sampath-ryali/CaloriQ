import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../shared/food_item.dart';
import 'auth/presentation/providers/auth_provider.dart';

const _apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:5000/api',
);

class FoodState {
  final FoodItem? food;
  final String? currentImageId;
  final bool isUploading;
  final String? error;

  FoodState({
    this.food,
    this.currentImageId,
    this.isUploading = false,
    this.error,
  });

  FoodState copyWith({
    FoodItem? food,
    String? currentImageId,
    bool? isUploading,
    String? error,
    bool clearError = false,
  }) {
    return FoodState(
      food: food ?? this.food,
      currentImageId: currentImageId ?? this.currentImageId,
      isUploading: isUploading ?? this.isUploading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class FoodNotifier extends StateNotifier<FoodState> {
  final Ref ref;

  FoodNotifier(this.ref) : super(FoodState());

  void setFood(FoodItem food) {
    state = state.copyWith(food: food);
  }

  Future<bool> uploadImage(String imagePath) async {
    state = state.copyWith(isUploading: true, clearError: true);

    try {
      final token = ref.read(authProvider).token;
      if (token == null || token.isEmpty) {
        state = state.copyWith(
          isUploading: false,
          error: 'Not authenticated. Please log in.',
        );
        return false;
      }

      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$_apiBaseUrl/upload-image'),
      );

      request.headers['Authorization'] = 'Bearer $token';
      request.files.add(await http.MultipartFile.fromPath('image', imagePath));

      final streamedResponse = await request.send().timeout(const Duration(seconds: 30));
      final response = await http.Response.fromStream(streamedResponse);

      final data = jsonDecode(response.body);

      if (response.statusCode == 201) {
        final imageId = data['image_id'];
        
        // Use the mock food generator for the visual result screen preview 
        // as per the requirement, but store the real imageId for the VQA chat.
        final food = FoodItem.fromImage(imagePath);
        
        state = state.copyWith(
          food: food,
          currentImageId: imageId,
          isUploading: false,
        );
        return true;
      } else {
        state = state.copyWith(
          isUploading: false,
          error: data['error_message'] ?? data['message'] ?? 'Image upload failed',
        );
        return false;
      }
    } catch (e) {
      state = state.copyWith(
        isUploading: false,
        error: 'Network error during upload: $e',
      );
      return false;
    }
  }

  void clear() {
    state = FoodState();
  }
}

final foodProvider = StateNotifierProvider<FoodNotifier, FoodState>((ref) {
  return FoodNotifier(ref);
});
