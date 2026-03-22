import 'package:flutter/material.dart';
import '../models/shop_item.dart';

class ShopItemTile extends StatelessWidget {
  final ShopItem item;

  const ShopItemTile({
    super.key,
    required this.item,
  });

  @override
  Widget build(BuildContext context) {
    final isBought = item.isBought; //샀느냐 안 샀느냐 따지는 필드 필요

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: BoxDecoration(
        color: isBought ? Colors.grey.shade200 : Colors.white,
        border: const Border(
          bottom: BorderSide(color: Color(0xFFE0E0E0)),
        ),
      ),
      child: Row(
        children: [
          // 🔲 아이템 네모 박스
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              color: isBought ? Colors.grey.shade300 : Colors.grey.shade200,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey.shade400),
            ),
            alignment: Alignment.center,
            child: const Text(
              'ITEM',
              style: TextStyle(fontSize: 12, color: Colors.black54),
            ),
          ),

          const SizedBox(width: 16),

          Expanded(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Row(
                  children: [
                    const Icon(
                      Icons.monetization_on,
                      size: 18,
                      color: Colors.amber,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '${item.priceCoin}',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: isBought ? Colors.grey : Colors.black,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
