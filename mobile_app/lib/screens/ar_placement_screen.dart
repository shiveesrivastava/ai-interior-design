import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:arcore_flutter_plus/arcore_flutter_plus.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:permission_handler/permission_handler.dart';
import 'package:vector_math/vector_math_64.dart' as vector;

// Real AR screen (Android / ARCore).
//
// ARCore scans the room and detects surfaces (floor, walls). The user taps a
// detected surface and the AI-generated image is pinned there as a thin,
// textured slab. Because it is anchored to the real world, it stays in place
// when the user walks around the room.
//
// Controls once placed:
//   - tap another spot on a surface -> move the image there
//   - pinch with two fingers        -> resize
//   - twist with two fingers        -> rotate freely
class ArPlacementScreen extends StatefulWidget {
  // Provide either the image bytes (normal case) or a link to download from.
  final Uint8List? imageBytes;
  final String? generatedImageUrl;

  const ArPlacementScreen({super.key, this.imageBytes, this.generatedImageUrl})
      : assert(
  imageBytes != null || generatedImageUrl != null,
  'Provide imageBytes or generatedImageUrl',
  );

  @override
  State<ArPlacementScreen> createState() => _ArPlacementScreenState();
}

class _ArPlacementScreenState extends State<ArPlacementScreen> {
  static const String _nodeName = 'generated_room_image';

  ArCoreController? _controller;

  Uint8List? _imageBytes;
  double _aspect = 1.5; // image width / height
  String? _error;

  // Where the user last tapped (pose of the detected surface).
  vector.Vector3? _anchorPosition;
  vector.Vector4? _anchorRotation;

  // ARCore only shows the camera once the user has allowed camera access.
  bool _cameraGranted = false;
  bool _cameraPermanentlyDenied = false;

  bool _placed = false;
  double _widthMeters = 1.0; // real-world width of the image
  double _yawRadians = 0.0; // rotation around the surface normal

  // The red surface dots are shown while scanning, then hidden after placing.
  bool _planesVisible = true;

  // Two-finger gesture tracking (pinch to resize, twist to rotate).
  final Map<int, Offset> _pointers = {};
  double _startDistance = 0;
  double _startAngle = 0;
  double _startWidth = 1.0;
  double _startYaw = 0.0;
  DateTime _lastApply = DateTime.fromMillisecondsSinceEpoch(0);

  @override
  void initState() {
    super.initState();
    _requestCamera();
    _loadImage();
  }

  Future<void> _requestCamera() async {
    final status = await Permission.camera.request();
    if (!mounted) return;
    setState(() {
      _cameraGranted = status.isGranted;
      _cameraPermanentlyDenied = status.isPermanentlyDenied;
    });
  }

  Widget _buildPermissionView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.camera_alt_outlined,
                color: Colors.white, size: 48),
            const SizedBox(height: 16),
            const Text(
              'Camera access is needed to show the design in your room.',
              style: TextStyle(color: Colors.white),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed:
              _cameraPermanentlyDenied ? openAppSettings : _requestCamera,
              child: Text(
                _cameraPermanentlyDenied ? 'Open settings' : 'Allow camera',
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Downloads the generated image so it can be used as an AR texture.
  Future<void> _loadImage() async {
    try {
      final Uint8List bytes;
      if (widget.imageBytes != null) {
        bytes = widget.imageBytes!;
      } else {
        final response = await http.get(
          Uri.parse(widget.generatedImageUrl!),
          headers: {'ngrok-skip-browser-warning': 'true'},
        );
        if (response.statusCode != 200) {
          throw Exception('Image download failed (${response.statusCode})');
        }
        bytes = response.bodyBytes;
      }

      // Read the real width/height so the slab has the right proportions.
      final codec = await ui.instantiateImageCodec(bytes);
      final frame = await codec.getNextFrame();
      final aspect = frame.image.width / frame.image.height;

      if (!mounted) return;
      setState(() {
        _imageBytes = bytes;
        _aspect = aspect;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = "Couldn't load the generated image: $e");
    }
  }

  void _onArCoreViewCreated(ArCoreController controller) {
    _controller = controller;
    controller.onPlaneTap = _onPlaneTap;
  }

  // Tapping a surface places the image there. Tapping again moves it, keeping
  // the size and rotation the user already chose.
  void _onPlaneTap(List<ArCoreHitTestResult> hits) {
    if (hits.isEmpty || _imageBytes == null) return;
    final pose = hits.first.pose;
    _anchorPosition = vector.Vector3.copy(pose.translation);
    _anchorRotation = vector.Vector4.copy(pose.rotation);

    final firstPlacement = !_placed;
    _placeNode();

    // Hide the red scanning dots once the image is down.
    if (firstPlacement && _planesVisible) {
      _togglePlanes();
    }
  }

  // (Re)creates the image slab at the last tapped spot using the current
  // size and rotation. Used for first placement and for every adjustment.
  void _placeNode() {
    final controller = _controller;
    final position = _anchorPosition;
    final rot = _anchorRotation;
    final bytes = _imageBytes;
    if (controller == null || position == null || rot == null || bytes == null) {
      return;
    }

    if (_placed) {
      controller.removeNode(nodeName: _nodeName);
    }

    final width = _widthMeters;
    final height = width / _aspect;

    // Fully matte (no metal, no gloss) so the image isn't streaked with
    // reflections or uneven highlights from the room lighting.
    final material = ArCoreMaterial(
      color: Colors.white,
      textureBytes: bytes,
      metallic: 0.0,
      roughness: 1.0,
      reflectance: 0.0,
    );

    // Thin along Y: ARCore's surface pose has its Y axis pointing out of the
    // surface, so the slab lies flat on a floor or flush against a wall.
    final slab = ArCoreCube(
      materials: [material],
      size: vector.Vector3(width, 0.01, height),
    );

    final base = vector.Quaternion(rot.x, rot.y, rot.z, rot.w);
    final yaw = vector.Quaternion.axisAngle(
      vector.Vector3(0, 1, 0),
      _yawRadians,
    );
    final q = base * yaw;

    // Nudge the slab a few millimetres out of the surface so it doesn't
    // flicker/overlap with the detected-plane overlay (z-fighting).
    final normal = base.rotated(vector.Vector3(0, 1, 0));
    final liftedPosition = position + normal * 0.006;

    final node = ArCoreNode(
      name: _nodeName,
      shape: slab,
      position: liftedPosition,
      rotation: vector.Vector4(q.x, q.y, q.z, q.w),
    );

    controller.addArCoreNodeWithAnchor(node);
    if (!_placed) setState(() => _placed = true);
  }

  // ---- Two-finger gestures -------------------------------------------------

  void _onPointerDown(PointerDownEvent e) {
    _pointers[e.pointer] = e.position;
    if (_pointers.length == 2) _beginTwoFinger();
  }

  void _beginTwoFinger() {
    final pts = _pointers.values.toList();
    _startDistance = (pts[0] - pts[1]).distance;
    _startAngle = (pts[1] - pts[0]).direction;
    _startWidth = _widthMeters;
    _startYaw = _yawRadians;
  }

  void _onPointerMove(PointerMoveEvent e) {
    if (!_pointers.containsKey(e.pointer)) return;
    _pointers[e.pointer] = e.position;
    if (_pointers.length != 2 || !_placed || _startDistance < 10) return;

    final pts = _pointers.values.toList();
    final distance = (pts[0] - pts[1]).distance;
    final angle = (pts[1] - pts[0]).direction;

    _widthMeters = (_startWidth * distance / _startDistance).clamp(0.2, 4.0);
    // Negative so twisting clockwise turns the image clockwise on screen.
    _yawRadians = _startYaw - (angle - _startAngle);

    // Rebuilding the AR node is fairly heavy, so only do it ~8 times a second
    // while the fingers are moving. The final position is applied on release.
    final now = DateTime.now();
    if (now.difference(_lastApply).inMilliseconds > 120) {
      _lastApply = now;
      _placeNode();
    }
  }

  void _onPointerEnd(PointerEvent e) {
    final wasTwoFinger = _pointers.length == 2;
    _pointers.remove(e.pointer);
    if (wasTwoFinger && _placed) _placeNode();
  }

  // ---- Buttons -------------------------------------------------------------

  void _rotate90() {
    _yawRadians += math.pi / 2;
    _placeNode();
  }

  void _resize(double factor) {
    _widthMeters = (_widthMeters * factor).clamp(0.2, 4.0);
    _placeNode();
  }

  void _remove() {
    _controller?.removeNode(nodeName: _nodeName);
    setState(() => _placed = false);
    if (!_planesVisible) _togglePlanes(); // show the scan dots again
  }

  void _togglePlanes() {
    _controller?.togglePlaneRenderer().catchError((_) {});
    setState(() => _planesVisible = !_planesVisible);
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: const Text('View in AR'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
      ),
      body: _error != null
          ? Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            _error!,
            style: const TextStyle(color: Colors.white),
            textAlign: TextAlign.center,
          ),
        ),
      )
          : !_cameraGranted
          ? _buildPermissionView()
          : Stack(
        children: [
          ArCoreView(
            onArCoreViewCreated: _onArCoreViewCreated,
            enableTapRecognizer: true,
            enablePlaneRenderer: true,
            planeColor: Colors.red,
          ),
          // Watches for two-finger pinch/twist. It only observes touches
          // (it doesn't consume them), so single taps still reach ARCore.
          Positioned.fill(
            child: Listener(
              behavior: HitTestBehavior.translucent,
              onPointerDown: _onPointerDown,
              onPointerMove: _onPointerMove,
              onPointerUp: _onPointerEnd,
              onPointerCancel: _onPointerEnd,
            ),
          ),
          if (_imageBytes == null)
            const Center(
              child: CircularProgressIndicator(color: Colors.white),
            ),
          Positioned(
            top: 12,
            left: 16,
            right: 16,
            child: IgnorePointer(
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  _placed
                      ? 'Pinch to resize, twist two fingers to rotate, '
                      'tap another spot to move it.'
                      : 'Move your phone slowly to scan the room, then '
                      'tap a wall or floor to place the design.',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          ),
          Positioned(
            bottom: 24,
            left: 8,
            right: 8,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _ControlButton(
                  icon: Icons.remove,
                  label: 'Smaller',
                  onPressed: _placed ? () => _resize(1 / 1.2) : null,
                ),
                _ControlButton(
                  icon: Icons.add,
                  label: 'Bigger',
                  onPressed: _placed ? () => _resize(1.2) : null,
                ),
                _ControlButton(
                  icon: Icons.rotate_90_degrees_ccw,
                  label: 'Rotate',
                  onPressed: _placed ? _rotate90 : null,
                ),
                _ControlButton(
                  icon: _planesVisible
                      ? Icons.grid_off
                      : Icons.grid_on,
                  label: _planesVisible ? 'Hide dots' : 'Show dots',
                  onPressed: _togglePlanes,
                ),
                _ControlButton(
                  icon: Icons.delete_outline,
                  label: 'Remove',
                  onPressed: _placed ? _remove : null,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ControlButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onPressed;

  const _ControlButton({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        FloatingActionButton.small(
          heroTag: label,
          onPressed: onPressed,
          backgroundColor: onPressed == null ? Colors.grey : Colors.white,
          foregroundColor: Colors.black,
          child: Icon(icon),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(color: Colors.white, fontSize: 11),
        ),
      ],
    );
  }
}