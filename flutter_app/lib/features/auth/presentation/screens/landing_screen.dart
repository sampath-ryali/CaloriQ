import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class LandingScreen extends StatelessWidget {
  const LandingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(),
              
              Icon(
                Icons.restaurant_menu,
                size: 100,
                color: Theme.of(context).colorScheme.primary,
              ),
              
              const SizedBox(height: 24),
              
              Text(
                'Food Assistant',
                style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  fontSize: 48,
                ),
                textAlign: TextAlign.center,
              ),
              
              const SizedBox(height: 8),
              
              Text(
                'Your AI-Powered Food Companion',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Colors.grey,
                ),
                textAlign: TextAlign.center,
              ),
              
              const Spacer(),
              
              ElevatedButton(
                onPressed: () => context.push('/login'),
                child: const Text('Log in'),
              ),
              
              const SizedBox(height: 16),
              
              OutlinedButton(
                onPressed: () => context.push('/signup'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text('Sign up'),
              ),
              
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
