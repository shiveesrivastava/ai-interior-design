import 'package:flutter/material.dart';
import '../widgets/buttons.dart';
import 'upload_screen.dart';
import 'ar_placement_screen.dart';

// Developer-only shortcut. It is OFF unless the app is built with
//   flutter run --release --dart-define=AR_TEST=true
// A normal build (no flag) never shows the button, so there is nothing to
// remove before presenting.
const bool kArTest = bool.fromEnvironment('AR_TEST');
// Landing screen. Shows a welcome message and a button to start the
// upload -> style -> generate flow.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 40),
              Icon(
                Icons.auto_awesome_rounded,
                size: 48,
                color: colorScheme.primary,
              ),
              const SizedBox(height: 16),
              Text(
                'Redesign any room\nwith AI',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Upload a photo of your room, pick a style, '
                    'and let AI generate a new look for it.',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: colorScheme.onSurfaceVariant,
                ),
              ),
              const Spacer(),
              // Simple illustration placeholder — replace with a real
              // asset/illustration later if desired.
              Center(
                child: Container(
                  width: 220,
                  height: 220,
                  decoration: BoxDecoration(
                    color: colorScheme.primaryContainer,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.home_work_rounded,
                    size: 100,
                    color: colorScheme.onPrimaryContainer,
                  ),
                ),
              ),
              const Spacer(),
              PrimaryButton(
                label: 'Get Started',
                icon: Icons.arrow_forward_rounded,
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const UploadScreen()),
                  );
                },
              ),
              if (kArTest) ...[
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => const ArPlacementScreen(
                          generatedImageUrl: 'https://picsum.photos/800/600',
                        ),
                      ),
                    );
                  },
                  child: const Text('AR test (sample image)'),
                ),
              ],
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}