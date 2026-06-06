import 'dart:io';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../domain/models/message.dart';
import '../screens/image_viewer_screen.dart';

class ChatBubble extends StatelessWidget {
  final Message message;

  const ChatBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            CircleAvatar(
              radius: 16,
              backgroundColor: isDark ? const Color(0xFF2D2D2D) : const Color(0xFFF7F7F8),
              child: Icon(
                Icons.smart_toy,
                size: 18,
                color: isDark ? Colors.white : Colors.black,
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Column(
              crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                if (message.isImage)
                  GestureDetector(
                    onTap: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (context) => ImageViewerScreen(
                            imagePath: message.imagePath!,
                          ),
                        ),
                      );
                    },
                    child: Container(
                      constraints: const BoxConstraints(
                        maxWidth: 250,
                        maxHeight: 300,
                      ),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(18).copyWith(
                          topLeft: isUser ? const Radius.circular(18) : const Radius.circular(4),
                          topRight: isUser ? const Radius.circular(4) : const Radius.circular(18),
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: isUser ? Colors.white70 : Colors.black.withValues(alpha: 0.5),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(18).copyWith(
                          topLeft: isUser ? const Radius.circular(18) : const Radius.circular(4),
                          topRight: isUser ? const Radius.circular(4) : const Radius.circular(18),
                        ),
                       child: message.imagePath!.startsWith('http')
                            ? Image.network(
                                message.imagePath!,
                                fit: BoxFit.cover,
                                errorBuilder: (context, error, stackTrace) => const Icon(
                                  Icons.broken_image,
                                  size: 48,
                                  color: Colors.grey,
                                ),
                              )
                            : Image.file(
                                File(message.imagePath!),
                                fit: BoxFit.cover,
                              ),
                      ),
                    ),
                  )
                else
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: isUser
                          ? (isDark ? Colors.white : Colors.black)
                          : (isDark ? const Color(0xFF2D2D2D) : const Color(0xFFF7F7F8)),
                      borderRadius: BorderRadius.circular(18).copyWith(
                        topLeft: isUser ? const Radius.circular(18) : const Radius.circular(4),
                        topRight: isUser ? const Radius.circular(4) : const Radius.circular(18),
                      ),
                    ),
                    child: Text(
                      message.text ?? '',
                      style: TextStyle(
                        color: isUser
                            ? (isDark ? Colors.black : Colors.white)
                            : (isDark ? Colors.white : Colors.black),
                        fontSize: 15,
                      ),
                    ),
                  ),
                const SizedBox(height: 4),
                Text(
                  DateFormat('HH:mm').format(message.timestamp),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey,
                        fontSize: 11,
                      ),
                ),
              ],
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 8),
            CircleAvatar(
              radius: 16,
              backgroundColor: isDark ? Colors.white : Colors.black,
              child: Icon(
                Icons.person,
                size: 18,
                color: isDark ? Colors.black : Colors.white,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
