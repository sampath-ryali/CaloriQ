import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../../../../core/network/api_client.dart';
import '../../domain/models/chat.dart';
import '../../domain/models/message.dart';

const _uuid = Uuid();

class ChatListNotifier extends StateNotifier<List<Chat>> {
  ChatListNotifier(this.ref) : super([]);

  final Ref ref;

  void addChat(Chat chat) {
    state = [chat, ...state];
  }

  void updateChat(Chat updatedChat) {
    state = [
      for (final chat in state)
        if (chat.id == updatedChat.id) updatedChat else chat,
    ];
  }

  void deleteChat(String chatId) {
    state = state.where((chat) => chat.id != chatId).toList();
  }

  Chat? getChatById(String id) {
    try {
      return state.firstWhere((chat) => chat.id == id);
    } catch (e) {
      return null;
    }
  }

  String createNewChat() {
    final newChatId = _uuid.v4();
    final newChat = Chat(
      id: newChatId,
      title: 'New Analysis',
      messages: [],
      createdAt: DateTime.now(),
    );
    addChat(newChat);
    return newChatId;
  }

  Future<void> loadChats() async {
    final api = ApiClient(ref);
    final data = await api.fetchChats();
    final rawChats = data['chats'];

    if (rawChats is! List) {
      return;
    }

    final loadedChats = rawChats
        .whereType<Map<String, dynamic>>()
        .map(
          (item) => Chat(
            id: (item['id'] ?? '').toString(),
            title: (item['title'] ?? 'New Analysis').toString(),
            messages: const [],
            createdAt: DateTime.tryParse((item['updated_at'] ?? item['created_at'] ?? '').toString()) ?? DateTime.now(),
          ),
        )
        .where((chat) => chat.id.isNotEmpty)
        .toList();

    state = loadedChats;
  }

  Future<void> loadMessages(String chatId) async {
    final api = ApiClient(ref);
    final data = await api.fetchChatMessages(chatId);
    final rawMessages = data['messages'];

    if (rawMessages is! List) {
      return;
    }

    final mappedMessages = rawMessages
        .whereType<Map<String, dynamic>>()
        .map(
          (item) => Message(
            id: (item['id'] ?? _uuid.v4()).toString(),
            text: (item['content'] ?? '').toString(),
            isUser: (item['role'] ?? 'assistant').toString() == 'user',
            timestamp: DateTime.tryParse((item['created_at'] ?? '').toString()) ?? DateTime.now(),
          ),
        )
        .toList();

    final existing = getChatById(chatId);
    if (existing == null) {
      addChat(
        Chat(
          id: chatId,
          title: 'Chat',
          messages: mappedMessages,
          createdAt: DateTime.now(),
        ),
      );
      return;
    }

    updateChat(existing.copyWith(messages: mappedMessages));
  }
}

final chatListProvider = StateNotifierProvider<ChatListNotifier, List<Chat>>((ref) {
  return ChatListNotifier(ref);
});
