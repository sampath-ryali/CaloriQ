import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/camera_screen.dart';
// FoodResultScreen removed to bypass dummy screen and go direct to chat
// OLD IMPORT DISABLED: import '../../features/chat_screen.dart';
import '../../features/chat/presentation/screens/chat_screen.dart';
import '../../features/chat/presentation/screens/home_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/signup_screen.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';
import '../../features/profile_screen.dart';
import '../../features/health_stats_screen.dart';
import '../../features/settings_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  
  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      // Wait for auth initialization
      if (!authState.isInitialized) {
        return null;
      }

      final isLoggedIn = authState.isLoggedIn;
      final isGoingToLogin = state.matchedLocation == '/login';
      final isGoingToSignup = state.matchedLocation == '/signup';

      // If not logged in and not going to auth pages, redirect to login
      if (!isLoggedIn && !isGoingToLogin && !isGoingToSignup) {
        return '/login';
      }

      // If logged in and going to auth pages, redirect to home
      if (isLoggedIn && (isGoingToLogin || isGoingToSignup)) {
        return '/';
      }

      // No redirect needed
      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        name: 'camera',
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const CameraScreen(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(
              opacity: CurvedAnimation(
                parent: animation,
                curve: Curves.easeInOutCubic,
              ),
              child: child,
            );
          },
        ),
      ),
      // /result route removed - capture now goes directly to chat
      GoRoute(
        path: '/chat/:chatId',
        name: 'chat',
        pageBuilder: (context, state) {
          final chatId = state.pathParameters['chatId'] ?? 'default';
          return CustomTransitionPage(
            key: state.pageKey,
            child: ChatScreen(chatId: chatId),
            transitionsBuilder: (context, animation, secondaryAnimation, child) {
              // Smooth fade + slide from bottom
              return FadeTransition(
                opacity: CurvedAnimation(
                  parent: animation,
                  curve: Curves.easeInOutCubic,
                ),
                child: SlideTransition(
                  position: Tween<Offset>(
                    begin: const Offset(0, 0.05),
                    end: Offset.zero,
                  ).animate(CurvedAnimation(
                    parent: animation,
                    curve: Curves.fastOutSlowIn,
                  )),
                  child: child,
                ),
              );
            },
          );
        },
      ),
      GoRoute(
        path: '/chats',
        name: 'chat-history',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/login',
        name: 'login',
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const LoginScreen(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(
              opacity: CurvedAnimation(
                parent: animation,
                curve: Curves.easeInOutCubic,
              ),
              child: child,
            );
          },
        ),
      ),
      GoRoute(
        path: '/signup',
        name: 'signup',
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const SignupScreen(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(
              opacity: CurvedAnimation(
                parent: animation,
                curve: Curves.easeInOutCubic,
              ),
              child: child,
            );
          },
        ),
      ),
      GoRoute(
        path: '/profile',
        name: 'profile',
        builder: (context, state) => const ProfileScreen(),
      ),
      GoRoute(
        path: '/health',
        name: 'health',
        builder: (context, state) => const HealthStatsScreen(),
      ),
      GoRoute(
        path: '/settings',
        name: 'settings',
        builder: (context, state) => const SettingsScreen(),
      ),
    ],
  );
});
