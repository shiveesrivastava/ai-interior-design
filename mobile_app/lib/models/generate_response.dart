import 'dart:typed_data';

// What the app gets back from the backend's /generate endpoint.
//
// The backend (API contract v3.0) normally returns the image itself as raw
// bytes, so [imageBytes] is the main field. Older/other response shapes with
// a hosted image link are still supported through [outputUrl].
class GenerateResponse {
  final String status;
  final String requestId;
  final Uint8List? imageBytes;
  final String? outputUrl;
  final String? inputUrl;
  final bool cacheHit;
  final int processingTimeMs;

  GenerateResponse({
    required this.status,
    required this.requestId,
    this.imageBytes,
    this.outputUrl,
    this.inputUrl,
    required this.cacheHit,
    required this.processingTimeMs,
  });

  // True if there is something to show (image bytes or a link to one).
  bool get hasImage => imageBytes != null || outputUrl != null;

  // Builds a response from the raw image bytes the backend sends back.
  factory GenerateResponse.fromImageBytes(
      Uint8List bytes, {
        required int processingTimeMs,
        String requestId = '',
      }) {
    return GenerateResponse(
      status: 'success',
      requestId: requestId,
      imageBytes: bytes,
      cacheHit: false,
      processingTimeMs: processingTimeMs,
    );
  }

  // Builds a response from a JSON map that contains a hosted image link.
  factory GenerateResponse.fromJson(Map<String, dynamic> json) {
    return GenerateResponse(
      status: json['status'] ?? 'unknown',
      requestId: json['request_id'] ?? '',
      outputUrl: json['output_url'],
      inputUrl: json['input_url'],
      cacheHit: json['cache_hit'] ?? false,
      processingTimeMs: (json['processing_time_ms'] as num?)?.toInt() ?? 0,
    );
  }
}