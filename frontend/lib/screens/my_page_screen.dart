import 'package:flutter/material.dart';
import 'package:lifeseed/managers/user_data_manager.dart';
//백엔드에 맞춰 재디자인해야
class MyPageScreen extends StatefulWidget {
  const MyPageScreen({super.key});

  @override
  State<MyPageScreen> createState() => _MyPageScreenState();
}

class _MyPageScreenState extends State<MyPageScreen> {
  int userCoins = 0;
  String nickname = "사용자";

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F1E8),
      appBar: AppBar(title: const Text('마이페이지')),
      body: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 20),
            const CircleAvatar(radius: 50, child: Icon(Icons.person, size: 50)),
            const SizedBox(height: 12),

            ValueListenableBuilder<int>(
              valueListenable: UserDataManager.userCoins,
              //UserDataManager 같은 거 없음!
              builder: (context, coins, _) =>
                  Text(
                    "보유 코인: $coins",
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.bold),
                  ),
            ),

            ValueListenableBuilder<int>(
              valueListenable: UserDataManager.userHearts,
              builder: (context, hearts, _) =>
                  Text(
                    "캐릭터 호감도: $hearts",
                    style: const TextStyle(color: Colors.pinkAccent),
                  ),
            ),
          ],
        ),
      ),
    );
  }
}