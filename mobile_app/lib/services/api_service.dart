import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import '../models/generate_response.dart';

// Handles all communication with the FastAPI backend (API contract v3.0).
//
// baseUrl must point to wherever the backend is actually running.
// Do NOT include a trailing slash.
class ApiService {
  // Your PC's Wi-Fi address (from `ipconfig`). It can change when the
  // router reassigns it, so update it if the app stops reaching the backend.
  static const String baseUrl = "http://192.168.88.7:8000";

  // Sends the room photo and the user's style description to the backend and
  // waits for the generated image. Throws an Exception with a readable
  // message on failure.
  //
  // `style` is the free-text description typed by the user. It is sent as a
  // custom style (style=custom), which the backend requires to come with both
  // base_prompt and custom_style_prompt (3-500 characters each).
  static Future<GenerateResponse> generateDesign({
    required File imageFile,
    required String style,
  }) async {
    final uri = Uri.parse("$baseUrl/generate/");

    final request = http.MultipartRequest('POST', uri);
    request.headers['ngrok-skip-browser-warning'] = 'true';
    request.fields['base_prompt'] = style;
    request.fields['style'] = 'custom';
    request.fields['custom_style_prompt'] = style;
    request.fields['operation'] = 'redesign';
    request.fields['user_id'] = 'flutter_app_user';
    request.files.add(
      // The backend checks the content type, so send the real one.
      await http.MultipartFile.fromPath(
        'file',
        imageFile.path,
        contentType: _mediaTypeFor(imageFile.path),
      ),
    );

    final stopwatch = Stopwatch()..start();

    try {
      // Generation can take 30-120 seconds, so use a generous timeout.
      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 130),
      );
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final contentType = response.headers['content-type'] ?? '';

        // Normal case: the backend returns the image itself.
        if (contentType.startsWith('image/')) {
          return GenerateResponse.fromImageBytes(
            response.bodyBytes,
            processingTimeMs: stopwatch.elapsedMilliseconds,
          );
        }

        // Otherwise it is JSON: either a base64 image or a hosted image link.
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final base64Image = data['image_base64'];
        if (base64Image is String) {
          return GenerateResponse.fromImageBytes(
            base64Decode(base64Image),
            processingTimeMs: stopwatch.elapsedMilliseconds,
            requestId: data['request_id'] ?? '',
          );
        }
        return GenerateResponse.fromJson(data);
      } else if (response.statusCode == 400) {
        throw Exception(
          "The server didn't accept the request: ${_errorDetail(response)}",
        );
      } else if (response.statusCode == 503 || response.statusCode == 504) {
        throw Exception(
          "The AI server is busy or unavailable right now. Please try again in a bit.",
        );
      } else {
        throw Exception(
          "Something went wrong (code ${response.statusCode}). Please try again.",
        );
      }
    } on SocketException {
      throw Exception(
        "Couldn't reach the server. Check your internet connection and that the backend URL is correct.",
      );
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception("Unexpected error: $e");
    }
  }

  // Pulls the readable message out of FastAPI's {"detail": "..."} errors.
  static String _errorDetail(http.Response response) {
    try {
      final data = jsonDecode(response.body);
      final detail = data['detail'];
      if (detail is String) return detail;
    } catch (_) {}
    return "code ${response.statusCode}";
  }

  static MediaType _mediaTypeFor(String path) {
    final ext = path.toLowerCase().split('.').last;
    switch (ext) {
      case 'png':
        return MediaType('image', 'png');
      case 'webp':
        return MediaType('image', 'webp');
      default:
        return MediaType('image', 'jpeg');
    }
  }
}