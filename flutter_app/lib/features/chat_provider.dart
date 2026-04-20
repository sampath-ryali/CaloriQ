import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../shared/chat_message.dart';

class ChatNotifier extends StateNotifier<List<ChatMessage>> {
  ChatNotifier() : super([]);

  void sendMessage(String text) {
    final message = ChatMessage.text(
      id: const Uuid().v4(),
      sender: MessageSender.user,
      content: text,
    );

    state = [...state, message];
    _generateMockResponse();
  }

  void sendImage(String imagePath) {
    final message = ChatMessage.image(
      id: const Uuid().v4(),
      sender: MessageSender.user,
      imagePath: imagePath,
    );

    state = [...state, message];
    _generateImageResponse(imagePath);
  }

  void _generateMockResponse() {
    Future.delayed(const Duration(milliseconds: 800), () {
      final responses = [
        'That\'s a great question! This food item has a balanced nutritional profile.',
        'Based on the analysis, this meal contains moderate calories and good protein content.',
        'I recommend pairing this with some vegetables for added nutrients.',
        'This food is rich in healthy fats which are good for heart health.',
        'Consider the portion size - moderation is key for maintaining a balanced diet.',
      ];

      final response = ChatMessage.text(
        id: const Uuid().v4(),
        sender: MessageSender.assistant,
        content: responses[state.length % responses.length],
      );

      state = [...state, response];
    });
  }

  void _generateImageResponse(String imagePath) {
    Future.delayed(const Duration(milliseconds: 800), () {
      final response = ChatMessage.text(
        id: const Uuid().v4(),
        sender: MessageSender.assistant,
        content: 'This looks delicious! Based on the image, I estimate approximately 350-450 calories. Would you like a detailed nutritional breakdown?',
      );

      state = [...state, response];
    });
  }

  void clearChat() {
    state = [];
  }
}

final chatProvider = StateNotifierProvider<ChatNotifier, List<ChatMessage>>((ref) {
  return ChatNotifier();
});
