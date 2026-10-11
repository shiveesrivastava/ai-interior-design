import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

// Displays an image from a local file (the user's uploaded photo), raw bytes
// (the backend's generated result) or a network URL.
// Shows a loading spinner / error icon automatically for network images.
class ImageCard extends StatelessWidget {
  final File? localFile;
  final Uint8List? memoryBytes;
  final String? networkUrl;
  final double borderRadius;
  final double? height;

  const ImageCard({
    super.key,
    this.localFile,
    this.memoryBytes,
    this.networkUrl,
    this.borderRadius = 20,
    this.height,
  }) : assert(
  localFile != null || memoryBytes != null || networkUrl != null,
  'Provide a localFile, memoryBytes or networkUrl',
  );

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: SizedBox(
        width: double.infinity,
        height: height,
        child: localFile != null
            ? Image.file(localFile!, fit: BoxFit.cover)
            : memoryBytes != null
            ? Image.memory(memoryBytes!, fit: BoxFit.cover)
            : CachedNetworkImage(
          imageUrl: networkUrl!,
          fit: BoxFit.cover,
          placeholder: (context, url) => Container(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            child: const Center(child: CircularProgressIndicator()),
          ),
          errorWidget: (context, url, error) => Container(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            child: const Center(
              child: Icon(Icons.broken_image_outlined, size: 40),
            ),
          ),
        ),
      ),
    );
  }
}