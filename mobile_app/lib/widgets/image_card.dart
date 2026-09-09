import 'dart:io';
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

// Displays an image, either from a local file (the user's uploaded photo)
// or from a network URL (the backend's generated result).
// Shows a loading spinner / error icon automatically for network images.
class ImageCard extends StatelessWidget {
  final File? localFile;
  final String? networkUrl;
  final double borderRadius;
  final double? height;

  const ImageCard({
    super.key,
    this.localFile,
    this.networkUrl,
    this.borderRadius = 20,
    this.height,
  }) : assert(
  localFile != null || networkUrl != null,
  'Provide either localFile or networkUrl',
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