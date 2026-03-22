//퀘스트 정보 모델 - ID, 코인/하트, 타입, 주간/일간
class ChecklistItem {
  final int id;
  final String text;
  final bool isDone;
  final int coinReward;
  final int affinityReward;
  final String type;   // study, sleep 등의 타입
  final String period; // daily, weekly, none
  final int targetValue;

  ChecklistItem({
    required this.id,
    required this.text,
    this.isDone = false,
    this.coinReward = 0,
    this.affinityReward = 0,
    required this.type,
    required this.period,
    this.targetValue = 0,
  });

  factory ChecklistItem.fromJson(Map<String, dynamic> json) {
    return ChecklistItem(
      id: json['id'],
      text: json['text'],
      isDone: json['isDone'] ?? false,
      coinReward: json['coinReward'] ?? 0,
      affinityReward: json['affinityReward'] ?? 0,
      type: json['type'] ?? 'etc',
      period: json['period'] ?? 'daily',
      targetValue: json['targetValue'] ?? 0,
    );
  }

  ChecklistItem copyWith({bool? isDone}) {
    return ChecklistItem(
      id: id,
      text: text,
      isDone: isDone ?? this.isDone,
      coinReward: coinReward,
      affinityReward: affinityReward,
      type: type,
      period: period,
      targetValue: targetValue,
    );
  }
}