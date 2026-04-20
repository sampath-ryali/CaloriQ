class UserProfile {
  final String id;
  final String name;
  final String email;
  final String? photoUrl;
  final String? bio;

  UserProfile({
    required this.id,
    required this.name,
    required this.email,
    this.photoUrl,
    this.bio,
  });

  UserProfile copyWith({
    String? name,
    String? email,
    String? photoUrl,
    String? bio,
  }) {
    return UserProfile(
      id: id,
      name: name ?? this.name,
      email: email ?? this.email,
      photoUrl: photoUrl ?? this.photoUrl,
      bio: bio ?? this.bio,
    );
  }

  factory UserProfile.guest() {
    return UserProfile(
      id: 'guest',
      name: 'Guest User',
      email: 'guest@foodlens.app',
    );
  }
}
