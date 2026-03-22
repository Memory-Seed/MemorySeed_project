//폰에서 모은 모든 라이프로그 묶어서 서버로 보내는 batch

class LifelogBatchRequest {
  final String runAt;
  final LocationData location;
  final List<StepData> steps;
  final List<SleepData> sleeps;
  final List<ScreenTimeData> screenTimes;
  final List<TransactionData> transactions;

  LifelogBatchRequest({
    required this.runAt,
    required this.location,
    required this.steps,
    required this.sleeps,
    required this.screenTimes,
    required this.transactions,
  });

  Map<String, dynamic> toJson() => {
    "runAt": runAt,
    "location": location.toJson(),
    "steps": steps.map((i) => i.toJson()).toList(),
    "sleeps": sleeps.map((i) => i.toJson()).toList(),
    "screenTimes": screenTimes.map((i) => i.toJson()).toList(),
    "transactions": transactions.map((i) => i.toJson()).toList(),
  };
}

class LocationData {
  final double lat;
  final double lon;
  LocationData({required this.lat, required this.lon});
  Map<String, dynamic> toJson() => {"lat": lat, "lon": lon};
}

class StepData {
  final String startTime;
  final String endTime;
  final int count;
  StepData({required this.startTime, required this.endTime, required this.count});
  Map<String, dynamic> toJson() => {"startTime": startTime, "endTime": endTime, "count": count};
}

class SleepData {
  final String startTime;
  final String endTime;
  SleepData({required this.startTime, required this.endTime});
  Map<String, dynamic> toJson() => {"startTime": startTime, "endTime": endTime};
}

class ScreenTimeData {
  final String packageName;
  final int totalTimeInForeground;
  final String sessionStart;
  final String sessionEnd;

  ScreenTimeData({
    required this.packageName,
    required this.totalTimeInForeground,
    required this.sessionStart,
    required this.sessionEnd,
  });

  Map<String, dynamic> toJson() => {
    "packageName": packageName,
    "totalTimeInForeground": totalTimeInForeground,
    "sessionStart": sessionStart,
    "sessionEnd": sessionEnd,
  };
}

class TransactionData {
  final String title;
  final int amount;
  final String transactionTime;

  TransactionData({
    required this.title,
    required this.amount,
    required this.transactionTime,
  });

  Map<String, dynamic> toJson() => {
    "title": title,
    "amount": amount,
    "transactionTime": transactionTime,
  };
}