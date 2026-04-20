class Message {
  final String id;
  final String? text;
  final String? imagePath;
  final bool isUser;
  final DateTime timestamp;

  Message({
    required this.id,
    this.text,
    this.imagePath,
    required this.isUser,
    required this.timestamp,
  });

  bool get isImage => imagePath != null && imagePath!.isNotEmpty;
  bool get isText => text != null && text!.isNotEmpty;

  Message copyWith({
    String? id,
    String? text,
    String? imagePath,
    bool? isUser,
    DateTime? timestamp,
  }) {
    return Message(
      id: id ?? this.id,
      text: text ?? this.text,
      imagePath: imagePath ?? this.imagePath,
      isUser: isUser ?? this.isUser,
      timestamp: timestamp ?? this.timestamp,
    );
  }
}
