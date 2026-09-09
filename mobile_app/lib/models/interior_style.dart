// Represents one interior design style the user can pick (e.g. "scandinavian").
class InteriorStyle {
  final String id;       // sent to backend as base_prompt
  final String label;    // shown to user
  final String emoji;    // small visual touch for the style chip

  const InteriorStyle({
    required this.id,
    required this.label,
    required this.emoji,
  });
}

// The 4 styles available in the backend config (config.py -> AVAILABLE_STYLES)
const List<InteriorStyle> availableStyles = [
  InteriorStyle(id: 'scandinavian', label: 'Scandinavian', emoji: '🪵'),
  InteriorStyle(id: 'royal', label: 'Royal', emoji: '👑'),
  InteriorStyle(id: 'industrial', label: 'Industrial', emoji: '🏭'),
  InteriorStyle(id: 'bohemian', label: 'Bohemian', emoji: '🌿'),
];