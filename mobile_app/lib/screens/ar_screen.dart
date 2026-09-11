import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

// Interactive AR-style overlay screen.
// Shows the live camera feed with the AI-generated room image floating
// on top. The user can drag, pinch-to-resize, and twist-to-rotate the
// overlay, plus adjust its opacity to blend it with the real room.
class ArScreen extends StatefulWidget {
  final String generatedImageUrl;

  const ArScreen({super.key, required this.generatedImageUrl});

  @override
  State<ArScreen> createState() => _ArScreenState();
}

class _ArScreenState extends State<ArScreen> {
  CameraController? _cameraController;
  bool _isCameraReady = false;
  String? _cameraError;

  // Current overlay transform
  Offset _position = Offset.zero;
  double _scale = 1.0;
  double _rotation = 0.0;
  double _opacity = 0.85;

  // Values captured at the start of a gesture, used to apply deltas smoothly
  Offset _startPosition = Offset.zero;
  double _startScale = 1.0;
  double _startRotation = 0.0;

  // Size of the draggable area, measured via LayoutBuilder, used to
  // keep the overlay from being dragged fully off-screen.
  Size _areaSize = Size.zero;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        setState(() => _cameraError = "No camera found on this device.");
        return;
      }

      final backCamera = cameras.firstWhere(
            (cam) => cam.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );

      final controller = CameraController(
        backCamera,
        ResolutionPreset.medium,
        enableAudio: false,
      );

      await controller.initialize();

      if (!mounted) return;

      setState(() {
        _cameraController = controller;
        _isCameraReady = true;
      });
    } catch (e) {
      setState(() => _cameraError = "Couldn't start the camera: $e");
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  void _resetOverlay() {
    setState(() {
      _position = Offset.zero;
      _scale = 1.0;
      _rotation = 0.0;
      _opacity = 0.85;
    });
  }

  // Keeps the overlay's center within a safe margin of the visible area,
  // so it can never be dragged fully out of sight.
  Offset _clampPosition(Offset proposed) {
    if (_areaSize == Size.zero) return proposed;

    // Allow the center point to travel most of the way to each edge,
    // leaving a small margin so it never fully disappears.
    final maxDx = (_areaSize.width / 2) - 40;
    final maxDy = (_areaSize.height / 2) - 40;

    return Offset(
      proposed.dx.clamp(-maxDx, maxDx),
      proposed.dy.clamp(-maxDy, maxDy),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: const Text("View in AR"),
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: "Reset Position",
            onPressed: _resetOverlay,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_cameraError != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            _cameraError!,
            style: const TextStyle(color: Colors.white),
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    if (!_isCameraReady || _cameraController == null) {
      return const Center(
        child: CircularProgressIndicator(color: Colors.white),
      );
    }

    return Column(
      children: [
        Expanded(
          child: LayoutBuilder(
            builder: (context, constraints) {
              // Keep track of the available area so we can clamp dragging.
              _areaSize = Size(constraints.maxWidth, constraints.maxHeight);

              return Stack(
                fit: StackFit.expand,
                clipBehavior: Clip.none,
                children: [
                  // Live camera feed
                  CameraPreview(_cameraController!),

                  // Draggable / pinchable / rotatable overlay image
                  GestureDetector(
                    onScaleStart: (details) {
                      _startPosition = _position;
                      _startScale = _scale;
                      _startRotation = _rotation;
                    },
                    onScaleUpdate: (details) {
                      setState(() {
                        final proposed =
                            _startPosition + details.focalPointDelta;
                        _position = _clampPosition(proposed);
                        _scale = (_startScale * details.scale).clamp(
                          0.2,
                          4.0,
                        );
                        _rotation = _startRotation + details.rotation;
                      });
                    },
                    child: Center(
                      child: Transform.translate(
                        offset: _position,
                        child: Transform.rotate(
                          angle: _rotation,
                          child: Transform.scale(
                            scale: _scale,
                            child: Opacity(
                              opacity: _opacity,
                              child: CachedNetworkImage(
                                imageUrl: widget.generatedImageUrl,
                                width: 280,
                                fit: BoxFit.contain,
                                placeholder: (context, url) => const SizedBox(
                                  width: 280,
                                  height: 280,
                                  child: Center(
                                    child: CircularProgressIndicator(),
                                  ),
                                ),
                                errorWidget: (context, url, error) =>
                                const Icon(
                                  Icons.broken_image,
                                  color: Colors.white,
                                  size: 60,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
        ),

        // Opacity control
        Container(
          color: Colors.black,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: Row(
            children: [
              const Icon(Icons.opacity, color: Colors.white, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Slider(
                  value: _opacity,
                  min: 0.1,
                  max: 1.0,
                  onChanged: (value) {
                    setState(() => _opacity = value);
                  },
                ),
              ),
            ],
          ),
        ),
        const Padding(
          padding: EdgeInsets.only(bottom: 12),
          child: Text(
            "Drag to move • Pinch to resize • Twist to rotate",
            style: TextStyle(color: Colors.white70, fontSize: 12),
          ),
        ),
      ],
    );
  }
}