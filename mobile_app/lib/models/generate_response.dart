// Represents the JSON response we get back from the backend's /generate endpoint.
// Matches the fields documented in backend/docs/api_contract.md and routes/generate.py
class GenerateResponse {
  final String status;
  final String requestId;
  final String? outputUrl;
  final String? inputUrl;
  final bool cacheHit;
  final int processingTimeMs;

  GenerateResponse({
    required this.status,
    required this.requestId,
    this.outputUrl,
    this.inputUrl,
    required this.cacheHit,
    required this.processingTimeMs,
  });

  // Factory constructor to build this object from a raw JSON map
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