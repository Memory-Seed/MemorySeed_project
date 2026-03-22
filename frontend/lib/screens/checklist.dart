import 'package:flutter/material.dart';
import '../widgets/checklist_widget.dart';
import 'package:lifeseed/widgets/user_status_bar.dart';
//퀘스트 화면 전체 레이아웃
class ChecklistScreen extends StatelessWidget {
  const ChecklistScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F1E8),
      appBar: AppBar(
        title: const Align(
          alignment: Alignment.centerRight,
          child: UserStatusBar(),
        ),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: const Padding(
        padding: EdgeInsets.all(16),
        child: ChecklistWidget(),
      ),
    );
  }
}
