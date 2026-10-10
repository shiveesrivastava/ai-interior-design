import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../models/interior_style.dart';
import '../widgets/buttons.dart';
import '../widgets/style_chip.dart';
import '../widgets/image_card.dart';
import 'loading_screen.dart';

// Lets the user pick a room photo (camera or gallery) and choose a style,
// then proceeds to the Loading screen to generate the design.
class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  File? _selectedImage;
  final TextEditingController _promptController = TextEditingController();
  final ImagePicker _picker = ImagePicker();

  // Limits enforced by the backend (config.py).
  static const int _minPromptLength = 3;
  static const int _maxPromptLength = 500;

  @override
  void initState() {
    super.initState();
    // Rebuild as the user types so the quick-idea highlight stays accurate.
    _promptController.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _promptController.dispose();
    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? picked = await _picker.pickImage(
        source: source,
        imageQuality: 90, // compress slightly to keep upload fast
      );
      if (picked != null) {
        setState(() {
          _selectedImage = File(picked.path);
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not access camera/gallery: $e')),
        );
      }
    }
  }

  void _showImageSourceSheet() {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Wrap(
            children: [
              ListTile(
                leading: const Icon(Icons.photo_camera_rounded),
                title: const Text('Take a photo'),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.camera);
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library_rounded),
                title: const Text('Choose from gallery'),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.gallery);
                },
              ),
            ],
          ),
        );
      },
    );
  }

  void _onContinue() {
    if (_selectedImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a photo first.')),
      );
      return;
    }
    final prompt = _promptController.text.trim();
    if (prompt.length < _minPromptLength) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please describe the style you want (a few words).'),
        ),
      );
      return;
    }
    Navigator.of(context).push(
      MaterialPageRoute(
        // LoadingScreen's `styleId` parameter now carries the full prompt text.
        builder: (_) => LoadingScreen(
          imageFile: _selectedImage!,
          styleId: prompt,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Upload Your Room')),
      body: SafeArea(
        child: SingleChildScrollView(
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Image picker area
              GestureDetector(
                onTap: _showImageSourceSheet,
                child: _selectedImage == null
                    ? Container(
                  width: double.infinity,
                  height: 240,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: Theme.of(context).colorScheme.outlineVariant,
                      style: BorderStyle.solid,
                    ),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.add_a_photo_rounded,
                        size: 40,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(height: 12),
                      const Text('Tap to add a room photo'),
                    ],
                  ),
                )
                    : Stack(
                  children: [
                    ImageCard(localFile: _selectedImage, height: 240),
                    Positioned(
                      top: 10,
                      right: 10,
                      child: CircleAvatar(
                        backgroundColor: Colors.black54,
                        child: IconButton(
                          icon: const Icon(Icons.edit, color: Colors.white, size: 18),
                          onPressed: _showImageSourceSheet,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 28),
              Text(
                'Describe your style',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _promptController,
                minLines: 3,
                maxLines: 5,
                maxLength: _maxPromptLength,
                textCapitalization: TextCapitalization.sentences,
                decoration: const InputDecoration(
                  hintText: 'e.g. Cozy modern living room with warm lighting, '
                      'light wood furniture and green plants',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Or start from a quick idea:',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: availableStyles.map((style) {
                  return StyleChip(
                    style: style,
                    isSelected: _promptController.text == style.prompt,
                    onTap: () => setState(
                          () => _promptController.text = style.prompt,
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 28),
              PrimaryButton(
                label: 'Generate Design',
                icon: Icons.auto_awesome_rounded,
                onPressed: _onContinue,
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}