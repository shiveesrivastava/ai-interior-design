import 'package:flutter/material.dart';
import 'home_screen.dart';

// First screen shown when the app opens. Displays briefly, then
// automatically navigates to the Home screen.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    // Wait 2 seconds, then move to Home. mounted check avoids navigating
    // after the widget has been disposed (e.g. user closed app quickly).
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const HomeScreen()),
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: colorScheme.primary,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.chair_alt_rounded,
              size: 80,
              color: colorScheme.onPrimary,
            ),
            const SizedBox(height: 20),
            Text(
              'AI Interior Designer',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: colorScheme.onPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Reimagine your space with AI',
              style: TextStyle(
                fontSize: 14,
                color: colorScheme.onPrimary.withValues(alpha: 0.8),
              ),
            ),
          ],
        ),
      ),
    );
  }
}