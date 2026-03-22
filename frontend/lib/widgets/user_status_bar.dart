import 'package:flutter/material.dart';
import '../managers/user_data_manager.dart';

class UserStatusBar extends StatelessWidget {
  const UserStatusBar({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha:0.9),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha:0.05), blurRadius: 4)
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.favorite, color: Colors.red, size: 18),
          const SizedBox(width: 4),
          ValueListenableBuilder<int>(
            valueListenable: UserDataManager.userHearts,
            builder: (context, value, child) => Text(
              '$value',
              style: const TextStyle(
                fontSize: 14,
                color: Colors.black,
                fontWeight: FontWeight.w600,
                decoration: TextDecoration.none,
              ),
            ),
          ),
          const SizedBox(width: 12),
          const Icon(Icons.monetization_on, color: Colors.amber, size: 18),
          const SizedBox(width: 4),
          ValueListenableBuilder<int>(
            valueListenable: UserDataManager.userCoins,
            builder: (context, value, child) => Text(
              '$value',
              style: const TextStyle(
                fontSize: 14,
                color: Colors.black,
                fontWeight: FontWeight.bold,
                decoration: TextDecoration.none,
              ),
            ),
          ),
        ],
      ),
    );
  }
}