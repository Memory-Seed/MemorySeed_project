import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/checklist_item.dart';
import '../managers/user_data_manager.dart';
import '../screens/lock_screen.dart';
import '../screens/sleep_screen.dart';
import '../services/api_service.dart';

class ChecklistWidget extends StatefulWidget {
  const ChecklistWidget({super.key});

  @override
  State<ChecklistWidget> createState() => _ChecklistWidgetState();
}

class _ChecklistWidgetState extends State<ChecklistWidget> {
  static const _lastRefreshKey = 'last_ai_refresh';

  List<ChecklistItem> manualItems = [];
  List<ChecklistItem> aiItems = [];
  DateTime? lastRefreshTime;
  final TextEditingController _controller = TextEditingController();
  bool _loaded = false;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    final prefs = await SharedPreferences.getInstance();
    final lastTime = prefs.getString(_lastRefreshKey);

    try {
      //퀘스트 목록
      final allQuests = await ApiService().getActiveQuests();

      setState(() {
        //  카테고리 분리
        //type - 'etc'나 'manual'이면 일반, 나머지는 AI(study/sleep)로 분류
        manualItems = allQuests.where((e) => e.type == 'etc' || e.type == 'manual').toList();
        aiItems = allQuests.where((e) => e.type == 'study' || e.type == 'sleep').toList();

        if (lastTime != null) lastRefreshTime = DateTime.parse(lastTime);
        _loaded = true;
      });
      _checkQuests();
    } catch (e) {
      debugPrint("데이터 로드 실패: $e");
      setState(() => _loaded = true);
    }
  }

  //AI 퀘스트 갱신
  Future<void> _generateAITodos() async {
    if (lastRefreshTime != null) {
      final difference = DateTime.now().difference(lastRefreshTime!);
      if (difference.inHours < 6) {
        final remaining = 6 - difference.inHours;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('새로운 퀘스트까지 $remaining시간 남았습니다.')),
        );
        return;
      }
    }

    await _loadAll(); // 서버 데이터

    setState(() {
      lastRefreshTime = DateTime.now();
    });

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_lastRefreshKey, lastRefreshTime!.toIso8601String());
  }

  // 보상 지급
  Future<void> _rewardUser(ChecklistItem item) async {
    await UserDataManager.syncWithServer();
  }

  //자동 체크(서버 PATCH 호출)
  void _checkQuests() async {
    void validate(List<ChecklistItem> list) async {
      for (int i = 0; i < list.length; i++) {
        if (list[i].isDone) continue;
        bool reached = false;

        if (list[i].type == 'study') {
          int cur = (list[i].period == 'daily') ? UserDataManager.todayStudyMinutes.value : UserDataManager.weeklyStudyMinutes.value;
          if (cur >= list[i].targetValue) reached = true;
        } else if (list[i].type == 'sleep') {
          if (UserDataManager.todaySleepHours.value >= list[i].targetValue) reached = true;
        }

        if (reached) {
          final success = await ApiService().completeQuest(list[i].id);
          if (success) {
            setState(() {
              list[i] = list[i].copyWith(isDone: true);
            });
            _rewardUser(list[i]);
          }
        }
      }
    }
    validate(manualItems);
    validate(aiItems);
  }

  @override
  Widget build(BuildContext context) {
    if (!_loaded) return const Center(child: CircularProgressIndicator());
    return Column(
      children: [
        _buildInputRow(),
        const SizedBox(height: 16),
        Expanded(
          child: ListView(
            children: [
              _buildSectionTitle('일반 퀘스트', Colors.orange),
              ...manualItems.asMap().entries.map((e) => _buildTile(e.key, e.value, false)),
              const SizedBox(height: 24),
              _buildAIHeader(),
              ...aiItems.asMap().entries.map((e) => _buildTile(e.key, e.value, true)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildTile(int index, ChecklistItem item, bool isAI) {
    Color themeColor = Colors.orange;
    if (item.period == 'daily') themeColor = Colors.blue;
    if (item.period == 'weekly') themeColor = Colors.green;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      decoration: BoxDecoration(
        color: themeColor.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: themeColor.withOpacity(0.2)),
      ),
      child: ListTile(
        leading: GestureDetector(
          onTap: () async {
            if (item.isDone) return;

            //자동 퀘스트 여부 판단 (study/sleep)
            bool isAutomatic = (item.type == 'study' || item.type == 'sleep');

            if (isAutomatic) {
              Widget s = (item.type == 'study') ? const LockScreen() : const SleepScreen();
              await Navigator.push(context, MaterialPageRoute(builder: (_) => s));
              _checkQuests();
            } else {
              //수동 체크 시 서버에 완료 보고
              final success = await ApiService().completeQuest(item.id);
              if (success) {
                setState(() {
                  if (isAI) aiItems[index] = item.copyWith(isDone: true);
                  else manualItems[index] = item.copyWith(isDone: true);
                });
                _rewardUser(item);
              }
            }
          },
          child: Icon(item.isDone ? Icons.check_circle : Icons.circle_outlined, color: themeColor, size: 28),
        ),
        title: Text(item.text, style: TextStyle(decoration: item.isDone ? TextDecoration.lineThrough : null, fontWeight: FontWeight.bold)),
        subtitle: (item.period == 'none')
            ? const Text('보상 없음', style: TextStyle(fontSize: 11))
            : Row(
          children: [
            const Icon(Icons.monetization_on, size: 14, color: Colors.amber),
            Text(' ${item.coinReward}  ', style: const TextStyle(fontSize: 12)),
            const Icon(Icons.favorite, size: 14, color: Colors.pinkAccent),
            Text(' ${item.affinityReward}', style: const TextStyle(fontSize: 12)),
          ],
        ),
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline, size: 20, color: Colors.grey),
          onPressed: () {
            // 우선 로컬에서만 삭제
            setState(() { if (isAI) aiItems.removeAt(index); else manualItems.removeAt(index); });
          },
        ),
      ),
    );
  }

  Widget _buildInputRow() {
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: _controller,
            decoration: InputDecoration(hintText: '퀘스트 추가...', filled: true, fillColor: Colors.white, border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none)),
          ),
        ),
        const SizedBox(width: 8),
        IconButton(
          onPressed: () async {
            if (_controller.text.isEmpty) return;

            // 퀘스트 생성 요청
            final newItem = await ApiService().createCustomQuest(_controller.text, 1);
            if (newItem != null) {
              setState(() {
                manualItems.add(newItem);
                _controller.clear();
              });
            }
          },
          icon: const Icon(Icons.add_box, color: Colors.orange, size: 40),
        )
      ],
    );
  }

  Widget _buildAIHeader() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text('AI 퀘스트', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue)),
        TextButton.icon(
          onPressed: _generateAITodos,
          icon: const Icon(Icons.refresh, size: 18),
          label: const Text('갱신 (6h)'),
        )
      ],
    );
  }

  Widget _buildSectionTitle(String title, Color color) {
    return Padding(padding: const EdgeInsets.symmetric(vertical: 8), child: Text(title, style: TextStyle(color: color, fontWeight: FontWeight.bold)));
  }
}