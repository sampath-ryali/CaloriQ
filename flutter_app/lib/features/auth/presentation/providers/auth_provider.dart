import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:caloriq/core/network/api_client.dart';
import '../../domain/models/user.dart';

class AuthState {
  final User? user;
  final String? token;
  final bool isLoading;
  final String? error;
  final bool isInitialized;

  AuthState({
    this.user,
    this.token,
    this.isLoading = false,
    this.error,
    this.isInitialized = false,
  });

  bool get isLoggedIn =>
    user != null && (token?.isNotEmpty ?? false);

  AuthState copyWith({
    User? user,
    String? token,
    bool? isLoading,
    String? error,
    bool? isInitialized,
    bool clearUser = false,
  }) {
    return AuthState(
      user: clearUser ? null : (user ?? this.user),
      token: clearUser ? null : (token ?? this.token),
      isLoading: isLoading ?? this.isLoading,
      error: error,
      isInitialized: isInitialized ?? this.isInitialized,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(AuthState()) {
    _initialize();
  }

  void clearError() {
    if (state.error == null) {
      return;
    }
    state = state.copyWith(error: null);
  }

  Future<void> _initialize() async {
    final prefs = await SharedPreferences.getInstance();
    final isLoggedIn = prefs.getBool('isLoggedIn') ?? false;
    
    if (isLoggedIn) {
      final userId = prefs.getString('userId') ?? '1';
      final userName = prefs.getString('userName') ?? 'User';
      final userEmail = prefs.getString('userEmail') ?? 'user@example.com';
      final token = prefs.getString('token');
      
      final user = User(
        id: userId,
        name: userName,
        email: userEmail,
      );
      
      state = state.copyWith(user: user, token: token, isInitialized: true);
    } else {
      state = state.copyWith(isInitialized: true);
    }
  }

  Future<bool> login(String email, String password) async {
    if (email.isEmpty || password.isEmpty) {
      state = state.copyWith(error: 'Please fill in all fields');
      return false;
    }

    if (!email.contains('@')) {
      state = state.copyWith(error: 'Please enter a valid email');
      return false;
    }

    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _postWithAutoDiscoveryRetry(
        '/auth/login',
        {
          'username': email,
          'password': password,
        },
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        final accessToken = data['access_token'];
        final backendUser = data['user'];
        final backendName = (backendUser['name'] ?? backendUser['full_name'] ?? backendUser['username'] ?? '').toString();
        
        final user = User(
          id: backendUser['id'].toString(),
          name: backendName,
          email: email,
        );

        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('isLoggedIn', true);
        await prefs.setString('userId', user.id);
        await prefs.setString('userName', user.name);
        await prefs.setString('userEmail', user.email);
        await prefs.setString('token', accessToken);

        state = state.copyWith(user: user, token: accessToken, isLoading: false);
        return true;
      } else {
        final backendError = data['error'];
        final backendErrorMessage = backendError is Map<String, dynamic>
            ? backendError['message']
            : null;
        state = state.copyWith(
          isLoading: false, 
          error: backendErrorMessage ?? data['error_message'] ?? data['message'] ?? 'Login failed',
        );
        return false;
      }
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Connection error: $e');
      return false;
    }
  }

  Future<bool> signup(String name, String email, String password) async {
    if (name.isEmpty || email.isEmpty || password.isEmpty) {
      state = state.copyWith(error: 'Please fill in all fields');
      return false;
    }

    if (!email.contains('@')) {
      state = state.copyWith(error: 'Please enter a valid email');
      return false;
    }

    if (password.length < 8) {
      state = state.copyWith(error: 'Password length should be atleast 8 characters');
      return false;
    }

    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _postWithAutoDiscoveryRetry(
        '/auth/register',
        {
          'username': email,
          'full_name': name,
          'password': password,
        },
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 201) {
        final accessToken = data['access_token'];
        final backendUser = data['user'];
        final backendName = (backendUser['name'] ?? backendUser['full_name'] ?? name).toString();
        
        final user = User(
          id: backendUser['id'].toString(),
          name: backendName,
          email: email,
        );

        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('isLoggedIn', true);
        await prefs.setString('userId', user.id);
        await prefs.setString('userName', user.name);
        await prefs.setString('userEmail', user.email);
        await prefs.setString('token', accessToken);

        state = state.copyWith(user: user, token: accessToken, isLoading: false);
        return true;
      } else {
        final backendError = data['error'];
        final backendErrorMessage = backendError is Map<String, dynamic>
            ? backendError['message']
            : null;
        state = state.copyWith(
          isLoading: false, 
          error: backendErrorMessage ?? data['error_message'] ?? data['message'] ?? 'Signup failed',
        );
        return false;
      }
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Connection error: $e');
      return false;
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    
    state = state.copyWith(clearUser: true);
  }

  Future<http.Response> _postWithAutoDiscoveryRetry(
    String path,
    Map<String, dynamic> payload,
  ) async {
    Future<http.Response> send() {
      return http.post(
        Uri.parse('${ApiConfig.baseUrl}$path'),
        headers: {
          'Content-Type': 'application/json',
          'bypass-tunnel-reminder': 'true',
        },
        body: jsonEncode(payload),
      );
    }

    try {
      return await send();
    } on SocketException {
      await ApiConfig.discoverAndSetReachableBaseUrl(forceRefresh: true);
      return send();
    } on TimeoutException {
      await ApiConfig.discoverAndSetReachableBaseUrl(forceRefresh: true);
      return send();
    }
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier();
});
