import 'dart:async';
import 'dart:convert'; // JSON 변환용
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/time_block.dart';
import 'package:lifeseed/widgets/user_status_bar.dart';

class SleepScreen extends StatefulWidget {
  const SleepScreen({super.key});

  @override
  State<SleepScreen> createState() => _SleepScreenState();
}

class _SleepScreenState extends State<SleepScreen> {
  Timer? _timer;
  int? _selectedEmotionIndex;
  Duration elapsed = Duration.zero;

  late DateTime startTime;
  static const String _historyKey = 'time_blocks';

  @override
  void initState() {
    super.initState();
    startTime = DateTime.now();

    _startTimer();

    // 표정 고르기 팝업
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _showEmotionPopup();
    });
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() {
        elapsed += const Duration(seconds: 1);
      });
    });
  }

  Future<void> _saveSleepData() async {
    final prefs = await SharedPreferences.getInstance();
    final endTime = DateTime.now();

    //기존 저장된 리스트
    List<String> storedHistory = prefs.getStringList(_historyKey) ?? [];

    //타임 블록 생성 (수면 타입)
    TimeBlock newSession = TimeBlock(
      start: startTime,
      end: endTime,
      type: 'sleep', // 'sleep'으로 저장하여 타임라인에서 파란색으로 표시되게 함
    );

    // JSON 문자열로 변환, 리스트 추가
    storedHistory.add(jsonEncode(newSession.toMap()));

    await prefs.setStringList(_historyKey, storedHistory);
  }

  String _format(Duration d) {
    final h = d.inHours.toString().padLeft(2, '0');
    final m = (d.inMinutes % 60).toString().padLeft(2, '0');
    final s = (d.inSeconds % 60).toString().padLeft(2, '0');
    return '$h:$m:$s';
  }
  Widget _emotionIcon(
      IconData icon,
      int index,
      void Function(void Function()) dialogSetState,
      ) {
    final bool isSelected = _selectedEmotionIndex == index;

    return GestureDetector(
      onTap: () {
        dialogSetState(() {
          _selectedEmotionIndex = index;
        });

        Future.delayed(const Duration(milliseconds: 200), () {
          if (mounted) {
            Navigator.pop(context);
          }
        });
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 100),
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: isSelected
              ? Colors.black.withOpacity(0.1)
              : Colors.transparent,
        ),
        child: Icon(
          icon,
          size: 36,
          color: Colors.black,
        ),
      ),
    );
  }

  void _showEmotionPopup() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) {
        return StatefulBuilder(
          builder: (context, dialogSetState) {
            return Dialog(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
              ),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text(
                      '오늘도 잘 해냈어요.',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    const Text('오늘 하루를 어떻게 보냈나요?'),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        _emotionIcon(Icons.sentiment_very_dissatisfied, 0, dialogSetState),
                        _emotionIcon(Icons.sentiment_dissatisfied, 1, dialogSetState),
                        _emotionIcon(Icons.sentiment_neutral, 2, dialogSetState),
                        _emotionIcon(Icons.sentiment_satisfied, 3, dialogSetState),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F1E8),
      body: SafeArea(
        child: Stack(
          children: [
            //상단 상태 바
            Positioned(
              top: 16,
              right: 16,
              child: const UserStatusBar(),
            ),

            //캐릭터 + 타이머
            Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 240,
                    height: 240,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(24),
                    ),
                    alignment: Alignment.center,
                    child: const Text('CHARACTER_SLEEP', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _format(elapsed),
                    style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),

            //하단
            Positioned(
              left: 16,
              right: 16,
              bottom: 24,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onPressed: () async {
                  _timer?.cancel();
                  //수면 데이터 저장 후 화면 닫기
                  await _saveSleepData();
                  if (mounted) Navigator.pop(context);
                },
                child: const Text('측정 종료', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}