import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'auth/presentation/providers/auth_provider.dart';
import 'profile_provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider);
    final authUser = ref.watch(authProvider).user;
    final displayName = authUser?.name ?? profile.name;
    final displayEmail = authUser?.email ?? profile.email;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Profile Photo
            Center(
              child: Stack(
                children: [
                  CircleAvatar(
                    radius: 60,
                    backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                    backgroundImage: profile.photoUrl != null 
                        ? FileImage(File(profile.photoUrl!))
                        : null,
                    child: profile.photoUrl == null
                        ? Icon(
                            Icons.person,
                            size: 60,
                            color: Theme.of(context).colorScheme.onPrimaryContainer,
                          )
                        : null,
                  ),
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: CircleAvatar(
                      radius: 20,
                      backgroundColor: Theme.of(context).colorScheme.primary,
                      child: IconButton(
                        icon: Icon(
                          Icons.camera_alt,
                          size: 18,
                          color: Theme.of(context).colorScheme.onPrimary,
                        ),
                        onPressed: () => _pickImage(context, ref),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            // Name Field
            TextField(
              decoration: const InputDecoration(
                labelText: 'Name',
                prefixIcon: Icon(Icons.person_outline),
              ),
              controller: TextEditingController(text: displayName),
              readOnly: true,
            ),
            const SizedBox(height: 16),

            // Email Field
            TextField(
              decoration: const InputDecoration(
                labelText: 'Email',
                prefixIcon: Icon(Icons.email_outlined),
              ),
              controller: TextEditingController(text: displayEmail),
              keyboardType: TextInputType.emailAddress,
              readOnly: true,
            ),
            const SizedBox(height: 16),

            // Password Field
            TextField(
              decoration: const InputDecoration(
                labelText: 'Password',
                prefixIcon: Icon(Icons.lock_outline),
              ),
              obscureText: true,
              controller: TextEditingController(text: '••••••••'),
              enabled: false,
            ),
            const SizedBox(height: 32),

            // Save Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Profile is synced from your login account.')),
                  );
                },
                child: const Padding(
                  padding: EdgeInsets.all(16),
                  child: Text('Save Changes'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickImage(BuildContext context, WidgetRef ref) async {
    final picker = ImagePicker();
    final image = await picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      ref.read(profileProvider.notifier).updatePhoto(image.path);
    }
  }
}
