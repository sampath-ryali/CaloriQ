import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/chat_provider.dart';
import '../providers/chat_list_provider.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/chat_input.dart';
import '../../../../shared/widgets/app_drawer.dart';

class ChatScreen extends ConsumerStatefulWidget {
  final String chatId;

  const ChatScreen({super.key, required this.chatId});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (widget.chatId == 'default') {
        final newChatId = ref.read(chatListProvider.notifier).createNewChat();
        if (mounted) {
          context.go('/chat/$newChatId');
        }
        return;
      }

      await ref.read(chatListProvider.notifier).loadMessages(widget.chatId);
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      Future.delayed(const Duration(milliseconds: 100), () {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(chatProvider(widget.chatId));
    final chatNotifier = ref.read(chatNotifierProvider(widget.chatId));

    // If chat not found, wait for provider hydration from API.
    if (chat == null) {
      return Scaffold(
        drawer: const AppDrawer(),
        appBar: AppBar(
          title: const Text('Chat'),
        ),
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());

    return Scaffold(
      drawer: const AppDrawer(),
      appBar: AppBar(
        title: Text(chat.title),
        actions: [
          IconButton(
            icon: const Icon(Icons.more_vert),
            onPressed: () {
              // TODO: Add more options
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: chat.messages.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.chat_bubble_outline,
                          size: 80,
                          color: Colors.grey[400],
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Start a conversation',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                color: Colors.grey[600],
                              ),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: chat.messages.length,
                    itemBuilder: (context, index) {
                      final message = chat.messages[index];
                      return ChatBubble(message: message);
                    },
                  ),
          ),
          ChatInput(
            onSend: (text) async {
              await chatNotifier.sendMessage(text);
            },
            onImageSend: (imagePath) async {
              await chatNotifier.sendImageMessage(imagePath);
            },
          ),
        ],
      ),
    );
  }
}
