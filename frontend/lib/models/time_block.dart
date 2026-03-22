import 'dart:convert';

class TimeBlock {
  final DateTime start;
  final DateTime end;
  final String type; // 'study' 또는 'sleep'

  TimeBlock({required this.start, required this.end, required this.type});

  // 객체를 JSON(Map)으로 변환 (저장용)
  Map<String, dynamic> toMap() => {
    'start': start.toIso8601String(),
    'end': end.toIso8601String(),
    'type': type,
  };

  // JSON(Map)을 객체로 변환 (불러오기용)
  factory TimeBlock.fromMap(Map<String, dynamic> map) => TimeBlock(
    start: DateTime.parse(map['start']),
    end: DateTime.parse(map['end']),
    type: map['type'],
  );
}