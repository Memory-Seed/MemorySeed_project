import 'package:flutter/material.dart';
import '../models/shop_item.dart';

class ShopDetailScreen extends StatelessWidget {
  final ShopItem item;
  final bool isAlreadyOwned; // 구매 여부...
  final VoidCallback onBuy;

  const ShopDetailScreen({
    super.key,
    required this.item,
    required this.onBuy,
    this.isAlreadyOwned = false,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(item.name)),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 실제 에셋 이미지로 바꿔야
            Container(
              width: 180,
              height: 180,
              decoration: BoxDecoration(
                color: Colors.grey.shade200,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.shade300),
              ),
              alignment: Alignment.center,
              child: Image.asset(item.assetKey, errorBuilder: (context, error, stackTrace) {
                return const Icon(Icons.inventory_2, size: 50, color: Colors.grey);
              }),
            ),
            const SizedBox(height: 12),
            Text(item.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(
              '${item.priceCoin} 코인',
              style: const TextStyle(fontSize: 22, color: Colors.orange, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: 160,
              height: 48,
              child: ElevatedButton(
                onPressed: isAlreadyOwned ? null : onBuy,
                child: Text(isAlreadyOwned ? '소유 중' : '구매하기'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}