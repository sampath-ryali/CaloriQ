import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class ChatInput extends StatefulWidget {
  final Future<void> Function(String) onSend;
  final Future<void> Function(String) onImageSend;

  const ChatInput({
    super.key, 
    required this.onSend,
    required this.onImageSend,
  });

  @override
  State<ChatInput> createState() => _ChatInputState();
}

class _ChatInputState extends State<ChatInput> {
  final TextEditingController _controller = TextEditingController();
  final ImagePicker _picker = ImagePicker();
  bool _isLoading = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _handleSend() async {
    if (_controller.text.trim().isEmpty || _isLoading) return;

    final text = _controller.text;
    _controller.clear();
    
    setState(() => _isLoading = true);
    
    await widget.onSend(text);
    
    setState(() => _isLoading = false);
  }

  Future<void> _pickImage() async {
    try {
      final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
      if (image != null) {
        setState(() => _isLoading = true);
        await widget.onImageSend(image.path);
        setState(() => _isLoading = false);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to pick image')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withValues(alpha: 0.3),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            IconButton(
              icon: const Icon(Icons.image_outlined),
              onPressed: _isLoading ? null : _pickImage,
            ),
            Expanded(
              child: TextField(
                controller: _controller,
                decoration: InputDecoration(
                  hintText: 'Message',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                  filled: true,
                  fillColor: Theme.of(context).brightness == Brightness.dark
                      ? const Color(0xFF2D2D2D)
                      : Colors.grey[200],
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                ),
                maxLines: null,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _handleSend(),
                enabled: !_isLoading,
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: _isLoading
                  ? const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.black,
                      ),
                    )
                  : Icon(
                      Icons.send,
                      color: Theme.of(context).brightness == Brightness.dark
                          ? Colors.white
                          : Colors.black,
                    ),
              onPressed: _isLoading ? null : _handleSend,
            ),
          ],
        ),
      ),
    );
  }
}
