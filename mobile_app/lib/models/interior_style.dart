// Represents one interior design style the user can pick (e.g. "scandinavian").
class InteriorStyle {
  final String id;       // short name of the style
  final String label;    // shown to user
  final String emoji;    // small visual touch for the style chip
  final String prompt;   // full text dropped into the prompt box when tapped

  const InteriorStyle({
    required this.id,
    required this.label,
    required this.emoji,
    required this.prompt,
  });
}

// Quick-pick suggestions. Tapping one fills the prompt box; the user can then
// edit it freely (the backend accepts any prompt of 3-500 characters).
const List<InteriorStyle> availableStyles = [
  InteriorStyle(
    id: 'scandinavian',
    label: 'Scandinavian',
    emoji: '🪵',
    prompt: 'Scandinavian style room with light wood furniture, white walls, '
        'soft neutral textiles, cozy lighting and lots of natural light',
  ),
  InteriorStyle(
    id: 'royal',
    label: 'Royal',
    emoji: '👑',
    prompt: 'Royal luxurious room with ornate gold-trimmed furniture, rich '
        'velvet fabrics, a crystal chandelier and deep jewel tones',
  ),
  InteriorStyle(
    id: 'industrial',
    label: 'Industrial',
    emoji: '🏭',
    prompt: 'Industrial loft style room with exposed brick, black metal '
        'fixtures, leather furniture and warm Edison bulb lighting',
  ),
  InteriorStyle(
    id: 'bohemian',
    label: 'Bohemian',
    emoji: '🌿',
    prompt: 'Bohemian style room with layered patterned rugs, macrame, lots '
        'of indoor plants, rattan furniture and warm earthy colors',
  ),
];