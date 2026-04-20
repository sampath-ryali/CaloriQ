import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/chat_list_provider.dart';
import 'package:intl/intl.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(chatListProvider.notifier).loadChats();
    });
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inDays == 0) {
      return DateFormat('HH:mm').format(timestamp);
    } else if (difference.inDays == 1) {
      return 'Yesterday';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} days ago';
    } else {
      return DateFormat('MMM d').format(timestamp);
    }
  }

  @override
  Widget build(BuildContext context) {
    final chats = ref.watch(chatListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Food Assistant'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () {
              final chatId = ref.read(chatListProvider.notifier).createNewChat();
              context.push('/chat/$chatId');
            },
          ),
        ],
      ),
      body: chats.isEmpty
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
                    'No chats yet',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: Colors.grey[600],
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Start a new conversation',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.grey[500],
                        ),
                  ),
                ],
              ),
            )
          : ListView.builder(
              itemCount: chats.length,
              itemBuilder: (context, index) {
                final chat = chats[index];
                return ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Theme.of(context).brightness == Brightness.dark
                        ? const Color(0xFF2D2D2D)
                        : Colors.grey[200],
                    child: Icon(
                      Icons.chat,
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.white
                          : Colors.black,
                    ),
                  ),
                  title: Text(
                    chat.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    chat.lastMessage,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  trailing: Text(
                    _formatTimestamp(chat.createdAt),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey,
                        ),
                  ),
                  onTap: () => context.push('/chat/${chat.id}'),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          final chatId = ref.read(chatListProvider.notifier).createNewChat();
          context.push('/chat/$chatId');
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
