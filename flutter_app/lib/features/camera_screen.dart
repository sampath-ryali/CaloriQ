import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'package:go_router/go_router.dart';
import 'camera_provider.dart';
import '../../shared/widgets/app_drawer.dart';
import 'chat/presentation/providers/chat_list_provider.dart';
import 'chat/presentation/providers/chat_provider.dart';

class CameraScreen extends ConsumerWidget {
  const CameraScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cameraState = ref.watch(cameraProvider);

    if (!cameraState.hasPermission) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.camera_alt_outlined,
                  size: 100,
                  color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3),
                ),
                const SizedBox(height: 32),
                Text(
                  'Camera Permission Required',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                Text(
                  'FoodLens needs camera access to scan and analyze your food.',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: Colors.grey,
                  ),
                  textAlign: TextAlign.center,
                ),
                if (cameraState.error != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    cameraState.error!,
                    style: TextStyle(
                      color: Colors.red[700],
                      fontSize: 14,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
                const SizedBox(height: 32),
                if (cameraState.canRequestPermission)
                  ElevatedButton.icon(
                    onPressed: () => ref.read(cameraProvider.notifier).requestPermission(),
                    icon: const Icon(Icons.check_circle_outline),
                    label: const Text('Grant Permission'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                    ),
                  )
                else
                  ElevatedButton.icon(
                    onPressed: () => ref.read(cameraProvider.notifier).openSettings(),
                    icon: const Icon(Icons.settings),
                    label: const Text('Open Settings'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                    ),
                  ),
              ],
            ),
          ),
        ),
      );
    }

    if (!cameraState.isInitialized) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      drawer: const AppDrawer(),
      body: Stack(
        children: [
          // Camera Preview
          Positioned.fill(
            child: CameraPreview(cameraState.controller!),
          ),

          // Framing Box
          Center(
            child: Container(
              width: MediaQuery.of(context).size.width * 0.8,
              height: MediaQuery.of(context).size.width * 0.8,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white, width: 3),
                borderRadius: BorderRadius.circular(24),
              ),
            ),
          ),

          // Top Controls
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Menu Button
                  Builder(
                    builder: (context) => IconButton(
                      icon: const Icon(Icons.menu, color: Colors.white, size: 28),
                      onPressed: () => Scaffold.of(context).openDrawer(),
                    ),
                  ),
                  // Profile Button
                  IconButton(
                    icon: const Icon(Icons.account_circle, color: Colors.white, size: 28),
                    onPressed: () => context.push('/profile'),
                  ),
                ],
              ),
            ),
          ),

          // Bottom Controls
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    // Gallery Button
                    _ControlButton(
                      icon: Icons.photo_library,
                      onPressed: () => _pickFromGallery(context, ref),
                    ),
                    
                    // Capture Button
                    GestureDetector(
                      onTap: () => _takePicture(context, ref),
                      child: Container(
                        width: 70,
                        height: 70,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.white,
                          border: Border.all(color: Colors.white, width: 4),
                        ),
                        child: Container(
                          margin: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                        ),
                      ),
                    ),
                    
                    // Flash Button
                    _ControlButton(
                      icon: cameraState.isFlashOn ? Icons.flash_on : Icons.flash_off,
                      onPressed: () => ref.read(cameraProvider.notifier).toggleFlash(),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // Floating Buttons
          Positioned(
            right: 16,
            bottom: 140,
            child: Column(
              children: [
                FloatingActionButton(
                  heroTag: 'chat',
                  mini: true,
                  backgroundColor: Colors.white.withValues(alpha: 0.9),
                  onPressed: () => context.push('/chats'),
                  child: const Icon(Icons.chat, color: Colors.black87),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _takePicture(BuildContext context, WidgetRef ref) async {
    final imagePath = await ref.read(cameraProvider.notifier).takePicture();
    if (imagePath != null && context.mounted) {
      _processImage(context, ref, imagePath);
    }
  }

  Future<void> _pickFromGallery(BuildContext context, WidgetRef ref) async {
    final picker = ImagePicker();
    final image = await picker.pickImage(source: ImageSource.gallery);
    if (image != null && context.mounted) {
      _processImage(context, ref, image.path);
    }
  }

  void _processImage(BuildContext context, WidgetRef ref, String imagePath) {
    
    final chatListNotifier = ref.read(chatListProvider.notifier);
    final newChatId = chatListNotifier.createNewChat();
    
    context.push('/chat/$newChatId');
    
    final chatNotifier = ref.read(chatNotifierProvider(newChatId));
    chatNotifier.sendImageMessage(imagePath);
  }
}

class _ControlButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onPressed;

  const _ControlButton({
    required this.icon,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.black.withValues(alpha: 0.5),
      ),
      child: IconButton(
        icon: Icon(icon, color: Colors.white, size: 28),
        onPressed: onPressed,
      ),
    );
  }
}
