import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/response_parser.dart';
import '../../domain/models/chat.dart';
import '../../domain/models/message.dart';
import 'chat_list_provider.dart';
import '../../../food_provider.dart';

const _uuid = Uuid();

final chatProvider = Provider.family<Chat?, String>((ref, chatId) {
  final chats = ref.watch(chatListProvider);
  try {
    return chats.firstWhere((chat) => chat.id == chatId);
  } catch (e) {
    return null;
  }
});

class ChatNotifier {
  ChatNotifier(this.ref, this.chatId);

  final Ref ref;
  final String chatId;

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    final chatListNotifier = ref.read(chatListProvider.notifier);
    final currentChat = chatListNotifier.getChatById(chatId);
    
    if (currentChat == null) return;

    final userMessage = Message(
      id: _uuid.v4(),
      text: text,
      isUser: true,
      timestamp: DateTime.now(),
    );

    final updatedMessages = [...currentChat.messages, userMessage];
    
    String title = currentChat.title;
    if (currentChat.messages.isEmpty) {
      title = text.length > 30 ? '${text.substring(0, 30)}...' : text;
    }

    chatListNotifier.updateChat(
      currentChat.copyWith(
        messages: updatedMessages,
        title: title,
      ),
    );

    final imageId = ref.read(foodProvider).currentImageId;
    
    if (imageId == null || imageId.isEmpty) {
      final errorMsg = Message(
        id: _uuid.v4(),
        text: 'Please take a photo or select an image of your food first before asking questions.',
        isUser: false,
        timestamp: DateTime.now(),
      );
      
      final finalChat = chatListNotifier.getChatById(chatId);
      if (finalChat != null) {
        chatListNotifier.updateChat(
          finalChat.copyWith(
            messages: [...finalChat.messages, errorMsg],
          ),
        );
      }
      return;
    }

    final api = ApiClient(ref);
    final apiResponse = await api.askQuestion(
      imageId: imageId,
      question: text,
      chatId: chatId,
    );
    final assistantText = formatAssistantReply(apiResponse);

    final assistantMessage = Message(
      id: _uuid.v4(),
      text: assistantText,
      isUser: false,
      timestamp: DateTime.now(),
    );

    final finalChat = chatListNotifier.getChatById(chatId);
    if (finalChat != null) {
      chatListNotifier.updateChat(
        finalChat.copyWith(
          messages: [...finalChat.messages, assistantMessage],
        ),
      );
    }
  }

  Future<void> sendImageMessage(String imagePath) async {
    if (imagePath.trim().isEmpty) return;

    final imageFile = File(imagePath);
    if (!imageFile.existsSync()) {
      return;
    }

    // Since we picked a new image inside the chat, we need to upload it first to get an image_id
    // and then we can optionally ask a generic question or wait for user.
    // For now, we'll just show the image message in the UI and trigger the upload.
    final chatListNotifier = ref.read(chatListProvider.notifier);
    final currentChat = chatListNotifier.getChatById(chatId);
    
    if (currentChat == null) return;

    final userMessage = Message(
      id: _uuid.v4(),
      imagePath: imagePath,
      isUser: true,
      timestamp: DateTime.now(),
    );

    final updatedMessages = [...currentChat.messages, userMessage];
    
    String title = currentChat.title;
    if (currentChat.messages.isEmpty) {
      title = 'Food Image';
    }

    chatListNotifier.updateChat(
      currentChat.copyWith(
        messages: updatedMessages,
        title: title,
      ),
    );

    // Upload the new image to set the imageId in the food provider state
    final uploadSuccess = await ref.read(foodProvider.notifier).uploadImage(imagePath);
    
    if (uploadSuccess) {
      final assistantMessage = Message(
        id: _uuid.v4(),
        text: 'Image uploaded successfully! What would you like to know about it?',
        isUser: false,
        timestamp: DateTime.now(),
      );

      final finalChat = chatListNotifier.getChatById(chatId);
      if (finalChat != null) {
        chatListNotifier.updateChat(
          finalChat.copyWith(
            messages: [...finalChat.messages, assistantMessage],
          ),
        );
      }
    } else {
      final assistantMessage = Message(
        id: _uuid.v4(),
        text: 'Failed to upload image. Please try again.',
        isUser: false,
        timestamp: DateTime.now(),
      );

      final finalChat = chatListNotifier.getChatById(chatId);
      if (finalChat != null) {
        chatListNotifier.updateChat(
          finalChat.copyWith(
            messages: [...finalChat.messages, assistantMessage],
          ),
        );
      }
    }
  }

  Future<void> sendMessageWithImage(String text, String imagePath) async {
    if (text.trim().isEmpty && imagePath.trim().isEmpty) return;

    final imageFile = File(imagePath);
    if (!imageFile.existsSync()) {
      return;
    }

    final chatListNotifier = ref.read(chatListProvider.notifier);
    final currentChat = chatListNotifier.getChatById(chatId);

    if (currentChat == null) return;

    final userImageMessage = Message(
      id: _uuid.v4(),
      imagePath: imagePath,
      isUser: true,
      timestamp: DateTime.now(),
    );

    final updatedMessages = [...currentChat.messages, userImageMessage];

    String title = currentChat.title;
    if (currentChat.messages.isEmpty) {
      title = text.trim().isNotEmpty
          ? (text.length > 30 ? '${text.substring(0, 30)}...' : text)
          : 'Food Image';
    }

    chatListNotifier.updateChat(
      currentChat.copyWith(
        messages: updatedMessages,
        title: title,
      ),
    );

    // Upload image first
    final uploadSuccess = await ref.read(foodProvider.notifier).uploadImage(imagePath);
    
    if (!uploadSuccess) {
      final assistantMessage = Message(
        id: _uuid.v4(),
        text: 'Failed to upload image. Cannot analyze the question.',
        isUser: false,
        timestamp: DateTime.now(),
      );
      final finalChat = chatListNotifier.getChatById(chatId);
      if (finalChat != null) {
        chatListNotifier.updateChat(
          finalChat.copyWith(
            messages: [...finalChat.messages, assistantMessage],
          ),
        );
      }
      return;
    }

    final imageId = ref.read(foodProvider).currentImageId;
    if (imageId == null || imageId.isEmpty) return;

    final api = ApiClient(ref);
    final apiResponse = await api.askQuestion(
      imageId: imageId,
      question: text.isEmpty ? 'What is this food?' : text,
      chatId: chatId,
    );
    final assistantText = formatAssistantReply(apiResponse);

    final assistantMessage = Message(
      id: _uuid.v4(),
      text: assistantText,
      isUser: false,
      timestamp: DateTime.now(),
    );

    final finalChat = chatListNotifier.getChatById(chatId);
    if (finalChat != null) {
      chatListNotifier.updateChat(
        finalChat.copyWith(
          messages: [...finalChat.messages, assistantMessage],
        ),
      );
    }
  }

}

final chatNotifierProvider = Provider.family<ChatNotifier, String>((ref, chatId) {
  return ChatNotifier(ref, chatId);
});
