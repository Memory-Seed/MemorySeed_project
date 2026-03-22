class ShopItem {
  final String code;
  final String name;
  final String category;
  final int priceCoin;
  final String assetKey;
  final bool active;

  ShopItem({
    required this.code,
    required this.name,
    required this.category,
    required this.priceCoin,
    required this.assetKey,
    this.active = true,
  });

  factory ShopItem.fromJson(Map<String, dynamic> json) {
    return ShopItem(
      code: json['code'],
      name: json['name'],
      category: json['category'],
      priceCoin: json['priceCoin'],
      assetKey: json['assetKey'],
      active: json['active'] ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
    'code': code,
    'name': name,
    'category': category,
    'priceCoin': priceCoin,
    'assetKey': assetKey,
    'active': active,
  };
}