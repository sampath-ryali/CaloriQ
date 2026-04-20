import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../../features/auth/presentation/providers/auth_provider.dart';
import 'response_parser.dart';

class ApiConfig {
  static String get baseUrl {
    return const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://10.0.2.2:5000/api',
    );
  }
}

class ApiClient {
  ApiClient(this.ref);

  final Ref ref;

  String get baseUrl => ApiConfig.baseUrl;

  Future<Map<String, dynamic>> askQuestion({
    required String imageId,
    required String question,
    required String chatId,
  }) async {
    try {
      final token = ref.read(authProvider).token;

      if (token == null || token.isEmpty) {
        await ref.read(authProvider.notifier).logout();
        return {'response': 'Session expired. Please login again', 'source': 'client_auth'};
      }

      final headers = <String, String>{
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      };

      final response = await http
          .post(
            Uri.parse('$baseUrl/ask-question'),
            headers: headers,
            body: jsonEncode({
              'image_id': imageId,
              'question': question,
              'chat_id': chatId,
              'language': 'en',
            }),
          )
          .timeout(const Duration(seconds: 90));

      if (response.statusCode == 401) {
        ref.read(authProvider.notifier).logout();
        return {'response': 'Session expired. Please login again', 'source': 'client_auth'};
      }

      return safeJson(response.body);
    } catch (_) {
      return {
        'response': 'Sorry, something went wrong while asking the question',
        'source': 'client_network',
      };
    }
  }

  Future<Map<String, dynamic>> fetchChats() async {
    try {
      final token = ref.read(authProvider).token;

      if (token == null || token.isEmpty) {
        return {'chats': <dynamic>[]};
      }

      final response = await http.get(
        Uri.parse('$baseUrl/chats'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 401) {
        await ref.read(authProvider.notifier).logout();
        return {'chats': <dynamic>[]};
      }

      return safeJson(response.body);
    } catch (_) {
      return {'chats': <dynamic>[]};
    }
  }

  Future<Map<String, dynamic>> fetchChatMessages(String chatId) async {
    try {
      final token = ref.read(authProvider).token;

      if (token == null || token.isEmpty) {
        return {'messages': <dynamic>[]};
      }

      final response = await http.get(
        Uri.parse('$baseUrl/chats/$chatId/messages'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 401) {
        await ref.read(authProvider.notifier).logout();
        return {'messages': <dynamic>[]};
      }

      return safeJson(response.body);
    } catch (_) {
      return {'messages': <dynamic>[]};
    }
  }
}
