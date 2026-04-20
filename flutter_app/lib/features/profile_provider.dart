import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../shared/user_profile.dart';

class ProfileNotifier extends StateNotifier<UserProfile> {
  ProfileNotifier() : super(UserProfile.guest());

  void updateName(String name) {
    state = state.copyWith(name: name);
  }

  void updateEmail(String email) {
    state = state.copyWith(email: email);
  }

  void updatePhoto(String photoUrl) {
    state = state.copyWith(photoUrl: photoUrl);
  }
}

final profileProvider = StateNotifierProvider<ProfileNotifier, UserProfile>((ref) {
  return ProfileNotifier();
});
