import 'dart:convert';

Map<String, dynamic> safeJson(String raw) {
  try {
    final decoded = jsonDecode(raw);
    if (decoded is Map<String, dynamic>) {
      return decoded;
    }
  } catch (_) {
    // Return a safe fallback below.
  }
  return {'response': 'Sorry, something went wrong'};
}

Map<String, dynamic>? _extractErrorPayload(Map<String, dynamic> data) {
  final error = data['error'];
  if (error is Map<String, dynamic>) {
    return error;
  }
  return null;
}

String extractSource(Map<String, dynamic> data) {
  final source = data['source'];
  if (source is String && source.trim().isNotEmpty) {
    return source.trim();
  }

  final payload = data['data'];
  if (payload is Map<String, dynamic>) {
    final nestedSource = payload['source'];
    if (nestedSource is String && nestedSource.trim().isNotEmpty) {
      return nestedSource.trim();
    }
  }

  final error = _extractErrorPayload(data);
  if (error != null) {
    final errorCode = error['code'];
    if (errorCode is String && errorCode.trim().isNotEmpty) {
      return errorCode.trim();
    }
  }

  return 'unknown';
}

String formatAssistantReply(Map<String, dynamic> data) {
  final answer = extractReply(data);
  final source = extractSource(data);
  return '$answer\n\nSource: $source';
}

String extractReply(Map<String, dynamic> data) {
  // Backend returns: {"answer": "...", "confidence": "...", "insights": ["..."], "nutrition": {...}, "ocr_text": "..."}
  
  final answer = data['answer'];
  if (answer != null && answer is String && answer.trim().isNotEmpty) {
    return answer;
  }
  
  final response = data['response'];
  if (response is String && response.trim().isNotEmpty) {
    return response;
  }

  // Fallback if data is wrapped
  final payload = data['data'];
  if (payload is Map<String, dynamic>) {
    final nestedAnswer = payload['answer'];
    if (nestedAnswer is String && nestedAnswer.trim().isNotEmpty) {
      return nestedAnswer;
    }

    final nestedResponse = payload['response'];
    if (nestedResponse is String && nestedResponse.trim().isNotEmpty) {
      return nestedResponse;
    }
  }

  final error = _extractErrorPayload(data);
  if (error != null) {
    final message = error['message'];
    if (message is String && message.trim().isNotEmpty) {
      return message;
    }
  }

  return 'Sorry, I could not generate an answer at this time.';
}
