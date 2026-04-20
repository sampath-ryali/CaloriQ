import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:camera/camera.dart';
import 'package:permission_handler/permission_handler.dart';

enum PermissionStatus {
  granted,
  denied,
  permanentlyDenied,
  restricted,
}

class CameraState {
  final List<CameraDescription> cameras;
  final CameraController? controller;
  final bool isInitialized;
  final bool isFlashOn;
  final PermissionStatus permissionStatus;
  final String? error;

  CameraState({
    this.cameras = const [],
    this.controller,
    this.isInitialized = false,
    this.isFlashOn = false,
    this.permissionStatus = PermissionStatus.denied,
    this.error,
  });

  bool get hasPermission => permissionStatus == PermissionStatus.granted;
  bool get canRequestPermission => permissionStatus != PermissionStatus.permanentlyDenied;

  CameraState copyWith({
    List<CameraDescription>? cameras,
    CameraController? controller,
    bool? isInitialized,
    bool? isFlashOn,
    PermissionStatus? permissionStatus,
    String? error,
  }) {
    return CameraState(
      cameras: cameras ?? this.cameras,
      controller: controller ?? this.controller,
      isInitialized: isInitialized ?? this.isInitialized,
      isFlashOn: isFlashOn ?? this.isFlashOn,
      permissionStatus: permissionStatus ?? this.permissionStatus,
      error: error,
    );
  }
}

class CameraNotifier extends StateNotifier<CameraState> {
  CameraNotifier() : super(CameraState()) {
    _initialize();
  }

  Future<void> _initialize() async {
    try {
      final status = await Permission.camera.status;
      
      if (status.isGranted) {
        state = state.copyWith(permissionStatus: PermissionStatus.granted);
        await _initializeCameras();
      } else if (status.isPermanentlyDenied) {
        state = state.copyWith(permissionStatus: PermissionStatus.permanentlyDenied);
      } else if (status.isRestricted) {
        state = state.copyWith(permissionStatus: PermissionStatus.restricted);
      } else {
        state = state.copyWith(permissionStatus: PermissionStatus.denied);
      }
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> _initializeCameras() async {
    try {
      final cameras = await availableCameras();
      
      if (cameras.isEmpty) {
        state = state.copyWith(error: 'No cameras found on this device');
        return;
      }

      state = state.copyWith(cameras: cameras);
      await _initializeCamera(cameras.first);
    } catch (e) {
      state = state.copyWith(error: 'Failed to initialize camera: ${e.toString()}');
    }
  }

  Future<void> _initializeCamera(CameraDescription camera) async {
    try {
      final controller = CameraController(
        camera,
        ResolutionPreset.high,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await controller.initialize();
      // Ensure flash is OFF by default
      await controller.setFlashMode(FlashMode.off);
      state = state.copyWith(
        controller: controller,
        isInitialized: true,
        isFlashOn: false,
      );
    } catch (e) {
      state = state.copyWith(error: 'Camera initialization failed: ${e.toString()}');
    }
  }

  Future<void> requestPermission() async {
    try {
      final status = await Permission.camera.request();
      
      if (status.isGranted) {
        state = state.copyWith(
          permissionStatus: PermissionStatus.granted,
          error: null,
        );
        await _initializeCameras();
      } else if (status.isPermanentlyDenied) {
        state = state.copyWith(
          permissionStatus: PermissionStatus.permanentlyDenied,
          error: 'Camera permission permanently denied. Please enable it in settings.',
        );
      } else if (status.isRestricted) {
        state = state.copyWith(
          permissionStatus: PermissionStatus.restricted,
          error: 'Camera access is restricted on this device.',
        );
      } else {
        state = state.copyWith(
          permissionStatus: PermissionStatus.denied,
          error: 'Camera permission denied.',
        );
      }
    } catch (e) {
      state = state.copyWith(error: 'Permission request failed: ${e.toString()}');
    }
  }

  Future<void> openSettings() async {
    await openAppSettings();
  }

  Future<void> toggleFlash() async {
    if (state.controller == null) return;

    try {
      final newFlashMode = state.isFlashOn ? FlashMode.off : FlashMode.torch;
      await state.controller!.setFlashMode(newFlashMode);
      state = state.copyWith(isFlashOn: !state.isFlashOn);
    } catch (e) {
      state = state.copyWith(error: 'Flash error: ${e.toString()}');
    }
  }

  Future<String?> takePicture() async {
    if (state.controller == null || !state.controller!.value.isInitialized) {
      return null;
    }

    try {
      final image = await state.controller!.takePicture();
      return image.path;
    } catch (e) {
      state = state.copyWith(error: 'Failed to capture image: ${e.toString()}');
      return null;
    }
  }

  @override
  void dispose() {
    state.controller?.dispose();
    super.dispose();
  }
}

final cameraProvider = StateNotifierProvider<CameraNotifier, CameraState>((ref) {
  return CameraNotifier();
});
