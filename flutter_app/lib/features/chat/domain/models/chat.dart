import 'message.dart';

class Chat {
  final String id;
  final String title;
  final List<Message> messages;
  final DateTime createdAt;

  Chat({
    required this.id,
    required this.title,
    required this.messages,
    required this.createdAt,
  });

  Chat copyWith({
    String? id,
    String? title,
    List<Message>? messages,
    DateTime? createdAt,
  }) {
    return Chat(
      id: id ?? this.id,
      title: title ?? this.title,
      messages: messages ?? this.messages,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  String get lastMessage {
    if (messages.isEmpty) return 'No messages yet';
    final last = messages.last;
    if (last.isImage) return '📷 Photo';
    return last.text ?? 'Message';
  }
}
