import 'dart:async';
import 'dart:convert'; // JSON 변환용
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'app_list.dart';
import '../models/time_block.dart';
import 'package:lifeseed/widgets/user_status_bar.dart';

class LockScreen extends StatefulWidget {
  const LockScreen({super.key});

  @override
  State<LockScreen> createState() => _LockScreenState();
}

class _LockScreenState extends State<LockScreen> {
  Timer? _timer;
  Duration elapsed = Duration.zero;
  bool _loaded = false;

  late DateTime startTime;
  List<String?> allowedApps = List.filled(5, null);
  static const String _prefsKey = 'allowed_apps';
  static const String _historyKey = 'time_blocks';

  @override
  void initState() {
    super.initState();
    startTime = DateTime.now();
    _loadAllowedApps();
    _startTimer();
  }


  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() {
        elapsed += const Duration(seconds: 1);
      });
    });
  }

  String _format(Duration d) {
    final h = d.inHours.toString().padLeft(2, '0');
    final m = (d.inMinutes % 60).toString().padLeft(2, '0');
    final s = (d.inSeconds % 60).toString().padLeft(2, '0');
    return '$h:$m:$s';
  }

  Future<void> _loadAllowedApps() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getStringList(_prefsKey);

    if (saved != null && saved.length == 5) {
      allowedApps = saved.map((e) => e.isEmpty ? null : e).toList();
    }

    setState(() {
      _loaded = true;
    });
  }

  Future<void> _saveAllowedApps() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      _prefsKey,
      allowedApps.map((e) => e ?? '').toList(),
    );
  }

  Future<void> _saveStudyData() async {
    final prefs = await SharedPreferences.getInstance();
    final endTime = DateTime.now();

    List<String> storedHistory = prefs.getStringList(_historyKey) ?? [];

    TimeBlock newSession = TimeBlock(
      start: startTime,
      end: endTime,
      type: 'study',
    );

    storedHistory.add(jsonEncode(newSession.toMap()));

    await prefs.setStringList(_historyKey, storedHistory);
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_loaded) {
      return const Scaffold(
        backgroundColor: Color(0xFFF6F1E8),
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF6F1E8),
      body: SafeArea(
        child: Stack(
          children: [
            Positioned(
              top: 16,
              right: 16,
              child: const UserStatusBar(),
            ),

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
                    child: const Text(
                      'CHARACTER_STUDY',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _format(elapsed),
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 20),
                  // 허용 앱
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: const [
                        BoxShadow(color: Colors.black12, blurRadius: 6),
                      ],
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: List.generate(5, (index) {
                        final app = allowedApps[index];
                        return Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 6),
                          child: InkWell(
                            borderRadius: BorderRadius.circular(24),
                            onTap: () async {
                              final result = await Navigator.push<String>(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => AppSelectScreen(
                                    selectedApps: allowedApps,
                                    index: index,
                                  ),
                                ),
                              );
                              if (result != null) {
                                setState(() {
                                  allowedApps[index] = result;
                                });
                                _saveAllowedApps();
                              }
                            },
                            child: Ink(
                              width: 48,
                              height: 48,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: app == null
                                    ? Colors.grey.shade200
                                    : Colors.green.shade200,
                              ),
                              child: Center(
                                child: app == null
                                    ? const Icon(Icons.add)
                                    : Text(app, style: const TextStyle(fontSize: 12)),
                              ),
                            ),
                          ),
                        );
                      }),
                    ),
                  ),
                ],
              ),
            ),

            //종료
            Positioned(
              left: 16,
              right: 16,
              bottom: 24,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black,
                  minimumSize: const Size(double.infinity, 50),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onPressed: () async {
                  _timer?.cancel();
                  //데이터 저장 후 화면 닫기
                  await _saveStudyData();
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