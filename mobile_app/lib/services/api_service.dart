import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/generate_response.dart';
<<<<<<< HEAD
import 'package:http_parser/http_parser.dart';
=======
>>>>>>> origin/main

// Handles all communication with the FastAPI backend.
//
// IMPORTANT: baseUrl must point to wherever the backend is actually running
// (e.g. an ngrok URL your backend teammate gives you, like
// "https://abcd-1234.ngrok-free.app"). Do NOT include a trailing slash.
class ApiService {
  // TODO: replace this with the real backend URL before testing Phase 5.
<<<<<<< HEAD
  //NEED TO CHANGE LATER// //THE URL NGROK LINK CHANGE//
  static const String baseUrl = "http://127.0.0.1:8000";
=======
  static const String baseUrl = "https://wackiness-spoils-manhunt.ngrok-free.dev";
>>>>>>> origin/main

  // Sends the selected image + style to the backend and waits for the
  // generated result. Throws an Exception with a readable message on failure.
  static Future<GenerateResponse> generateDesign({
    required File imageFile,
    required String style,
  }) async {
    final uri = Uri.parse("$baseUrl/generate/");

    final request = http.MultipartRequest('POST', uri);
    request.headers['ngrok-skip-browser-warning'] = 'true';
    request.fields['base_prompt'] = style;
    request.fields['user_id'] = 'flutter_app_user';
    request.files.add(
<<<<<<< HEAD
      await http.MultipartFile.fromPath(
        'file',
        imageFile.path,
        contentType: MediaType('image', 'jpeg'),
      ),
=======
      await http.MultipartFile.fromPath('file', imageFile.path),
>>>>>>> origin/main
    );

    try {
      // The backend can take 30-120 seconds to respond (real ML generation),
      // so we set a generous timeout rather than Flutter's tiny default.
      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 130),
      );
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return GenerateResponse.fromJson(data);
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
}