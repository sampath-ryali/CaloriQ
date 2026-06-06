import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../../features/auth/presentation/providers/auth_provider.dart';
import 'response_parser.dart';

class ApiConfig {
  static const String _prefsKey = 'api_base_url_override';
  static const String _autoDiscoverEnabledKey = 'api_auto_discover_enabled';
  static const int _defaultBackendPort = 5000;
  static String? _overrideBaseUrl;
  static final ValueNotifier<String?> discoveryStatus = ValueNotifier<String?>(null);

  static String get defaultBaseUrl {
    return const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://10.0.2.2:5000/api',
    );
  }

  static bool get hasOverride =>
      _overrideBaseUrl != null && _overrideBaseUrl!.isNotEmpty;

  static Future<bool> get autoDiscoverEnabled async {
    return false;
  }

  static Future<void> setAutoDiscoverEnabled(bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_autoDiscoverEnabledKey, enabled);
  }

  static String get baseUrl {
    return _overrideBaseUrl ?? defaultBaseUrl;
  }

  static Future<void> initialize() async {
    final prefs = await SharedPreferences.getInstance();
    final value = prefs.getString(_prefsKey);
    if (value != null && value.trim().isNotEmpty) {
      _overrideBaseUrl = _normalize(value);
    }
  }

  static Future<void> setBaseUrl(String url) async {
    final normalized = _normalize(url);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, normalized);
    _overrideBaseUrl = normalized;
  }

  static Future<void> clearOverride() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_prefsKey);
    _overrideBaseUrl = null;
  }

  static Future<String?> autoSelectReachableBaseUrl() async {
    if (!await autoDiscoverEnabled) {
      return null;
    }
    return discoverAndSetReachableBaseUrl(forceRefresh: false);
  }

  static Future<String?> discoverAndSetReachableBaseUrl({
    bool forceRefresh = true,
  }) async {
    _setDiscoveryStatus('Searching backend on local network...');
    final candidates = await _buildCandidates(forceRefresh: forceRefresh);
    final reachable = await _firstReachableCandidate(candidates);

    if (reachable != null) {
      await setBaseUrl(reachable);
      _setDiscoveryStatus('Connected to ${Uri.parse(reachable).host}');
      Future<void>.delayed(const Duration(seconds: 2), () {
        _setDiscoveryStatus(null);
      });
    } else {
      _setDiscoveryStatus('Could not find backend automatically');
      Future<void>.delayed(const Duration(seconds: 3), () {
        _setDiscoveryStatus(null);
      });
    }

    return reachable;
  }

  static Future<List<String>> _buildCandidates({required bool forceRefresh}) async {
    final ordered = <String>[];
    final seen = <String>{};

    void addCandidate(String? url) {
      if (url == null || url.trim().isEmpty) {
        return;
      }
      final normalized = _normalize(url);
      if (seen.add(normalized)) {
        ordered.add(normalized);
      }
    }

    addCandidate(_overrideBaseUrl);
    addCandidate(defaultBaseUrl);
    addCandidate('http://10.0.2.2:$_defaultBackendPort/api');
    addCandidate('http://127.0.0.1:$_defaultBackendPort/api');

    final discoveredHosts = await _localSubnetHosts(includeBroadScan: forceRefresh);
    for (final host in discoveredHosts) {
      addCandidate('http://$host:$_defaultBackendPort/api');
    }

    if (!forceRefresh && _overrideBaseUrl != null) {
      // Prioritize persisted override if still reachable.
      return [_overrideBaseUrl!, ...ordered.where((u) => u != _overrideBaseUrl)];
    }

    return ordered;
  }

  static Future<List<String>> _localSubnetHosts({
    required bool includeBroadScan,
  }) async {
    final hosts = <String>[];
    final seen = <String>{};

    void addHost(String host) {
      if (seen.add(host)) {
        hosts.add(host);
      }
    }

    try {
      final interfaces = await NetworkInterface.list(
        type: InternetAddressType.IPv4,
        includeLinkLocal: false,
      );

      for (final interface in interfaces) {
        final name = interface.name.toLowerCase();
        if (name.contains('rmnet') || name.contains('pdp') || name.contains('tun')) {
          continue;
        }

        for (final address in interface.addresses) {
          if (!_isPrivateIPv4(address)) {
            continue;
          }

          final octets = address.address.split('.');
          if (octets.length != 4) {
            continue;
          }

          final prefix = '${octets[0]}.${octets[1]}.${octets[2]}';
          final current = int.tryParse(octets[3]) ?? 0;

          // Fast path first: likely gateway and common laptop addresses.
          for (final tail in <int>[1, 2, 5, 6, 10, 20, 30, 40]) {
            if (tail != current && tail >= 1 && tail <= 254) {
              addHost('$prefix.$tail');
            }
          }

          // Nearby hosts in the same subnet are commonly active devices.
          for (var i = current - 20; i <= current + 20; i++) {
            if (i <= 1 || i >= 255 || i == current) {
              continue;
            }
            addHost('$prefix.$i');
          }

          // Broader scan fallback only during explicit retry.
          if (includeBroadScan) {
            for (var i = 2; i <= 254; i++) {
              if (i == current) {
                continue;
              }
              addHost('$prefix.$i');
            }
          }
        }
      }
    } catch (_) {
      return <String>[];
    }

    return hosts;
  }

  static bool _isPrivateIPv4(InternetAddress address) {
    if (address.type != InternetAddressType.IPv4 || address.isLoopback) {
      return false;
    }

    final octets = address.address.split('.');
    if (octets.length != 4) {
      return false;
    }

    final a = int.tryParse(octets[0]) ?? -1;
    final b = int.tryParse(octets[1]) ?? -1;

    return a == 10 ||
        (a == 172 && b >= 16 && b <= 31) ||
        (a == 192 && b == 168);
  }

  static Future<String?> _firstReachableCandidate(List<String> candidates) async {
    const batchSize = 24;
    final startedAt = DateTime.now();

    for (var i = 0; i < candidates.length; i += batchSize) {
      if (DateTime.now().difference(startedAt) > const Duration(seconds: 12)) {
        return null;
      }

      final batch = candidates.skip(i).take(batchSize).toList(growable: false);
      final result = await Future.wait(batch.map((url) async {
        final ok = await _isReachable(url);
        return ok ? url : null;
      }));

      for (final candidate in result) {
        if (candidate != null) {
          return candidate;
        }
      }
    }

    return null;
  }

  static void _setDiscoveryStatus(String? message) {
    if (discoveryStatus.value != message) {
      discoveryStatus.value = message;
    }
  }

  static Future<bool> _isReachable(String baseUrl) async {
    final healthUrl = '${_normalize(baseUrl).replaceFirst(RegExp(r'/api$'), '')}/health';
    final client = HttpClient()
      ..connectionTimeout = const Duration(milliseconds: 500);

    try {
      final request = await client.getUrl(Uri.parse(healthUrl));
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      final response = await request.close().timeout(const Duration(milliseconds: 700));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    } finally {
      client.close(force: true);
    }
  }

  static String _normalize(String url) {
    return url.trim().replaceFirst(RegExp(r'/+$'), '');
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
        'bypass-tunnel-reminder': 'true',
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
        headers: {
          'Authorization': 'Bearer $token',
          'bypass-tunnel-reminder': 'true',
        },
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
        headers: {
          'Authorization': 'Bearer $token',
          'bypass-tunnel-reminder': 'true',
        },
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
