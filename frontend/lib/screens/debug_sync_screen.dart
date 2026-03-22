import 'package:flutter/material.dart';
import '../models/lifelog_batch.dart';
import '../services/api_service.dart';
import '../services/lifelog_collector.dart';

class DebugSyncScreen extends StatefulWidget {
  const DebugSyncScreen({super.key});

  @override
  State<DebugSyncScreen> createState() => _DebugSyncScreenState();
}

class _DebugSyncScreenState extends State<DebugSyncScreen> {
  bool _isLoading = false;
  final List<StepData> _tempSteps = [
    StepData(startTime: "2026-03-22T08:00:00", endTime: "2026-03-22T08:10:00", count: 120),
    StepData(startTime: "2026-03-22T09:00:00", endTime: "2026-03-22T09:05:00", count: 50),
  ];

  void _showSnackBar(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Future<void> _handleSync() async {
    setState(() => _isLoading = true);

    try {
      LifelogCollector collector = LifelogCollector();
      LifelogBatchRequest fullRequest = await collector.collectAllData();

      final apiService = ApiService();
      final runId = await apiService.sendLifelogBatch(fullRequest);

      if (runId != null) {
        _showSnackBar("전송 성공! runId: $runId");
      } else {
        _showSnackBar("전송 실패: 서버 응답을 확인하세요.");
      }
    } catch (e) {
      _showSnackBar("에러 발생: $e");
      print("Sync Error: $e");
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("라이프로그 데이터 센터"),
        backgroundColor: Colors.blueGrey,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
                "현재 수집된 데이터 (임시)",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)
            ),
            const SizedBox(height: 10),
            Expanded(
              child: ListView.builder(
                itemCount: _tempSteps.length,
                itemBuilder: (context, index) {
                  final step = _tempSteps[index];
                  return Card(
                    elevation: 2,
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    child: ListTile(
                      leading: const CircleAvatar(
                        backgroundColor: Colors.blueAccent,
                        child: Icon(Icons.directions_walk, color: Colors.white),
                      ),
                      title: Text("${step.count} 걸음"),
                      subtitle: Text(
                          "${step.startTime.split('T')[1]} ~ ${step.endTime.split('T')[1]}"
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton.icon(
                onPressed: _isLoading ? null : _handleSync,
                style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))
                ),
                icon: _isLoading
                    ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)
                )
                    : const Icon(Icons.cloud_upload),
                label: Text(
                  _isLoading ? "서버와 통신 중..." : "서버로 데이터 동기화 시작",
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ),
            const SizedBox(height: 10),
            const Center(
              child: Text(
                "전송 시 위치, 걸음, 수면, 스크린타임이 모두 포함됩니다.",
                style: TextStyle(color: Colors.grey, fontSize: 12),
              ),
            )
          ],
        ),
      ),
    );
  }
}