enum MessageSender {
  user,
  assistant,
}

enum MessageType {
  text,
  image,
}

class ChatMessage {
  final String id;
  final MessageSender sender;
  final MessageType type;
  final String content;
  final String? imagePath;
  final DateTime timestamp;

  ChatMessage({
    required this.id,
    required this.sender,
    required this.type,
    required this.content,
    this.imagePath,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  factory ChatMessage.text({
    required String id,
    required MessageSender sender,
    required String content,
  }) {
    return ChatMessage(
      id: id,
      sender: sender,
      type: MessageType.text,
      content: content,
    );
  }

  factory ChatMessage.image({
    required String id,
    required MessageSender sender,
    required String imagePath,
    String? caption,
  }) {
    return ChatMessage(
      id: id,
      sender: sender,
      type: MessageType.image,
      content: caption ?? '',
      imagePath: imagePath,
    );
  }

  bool get isUser => sender == MessageSender.user;
  bool get isAssistant => sender == MessageSender.assistant;
  bool get isText => type == MessageType.text;
  bool get isImage => type == MessageType.image;
}
