//흩어진 데이터 모아서 전송용 객체로 변환하는 기능 (미완)
import 'package:geolocator/geolocator.dart';
import '../models/lifelog_batch.dart';
import 'package:pedometer/pedometer.dart';     // 걸음수
import 'package:app_usage/app_usage.dart';     // 스크린타임

class LifelogCollector {
  //함수
  Future<LifelogBatchRequest> collectAllData() async {

    //실행 시각
    String runAt = DateTime.now().toIso8601String().split('.')[0];

    //위치 가져오기
    Position position = await Geolocator.getCurrentPosition();
    LocationData location = LocationData(lat: position.latitude, lon: position.longitude);

    //DB에서 오늘치 읽어오기
    //databaseHelper.getSteps() 호출해야함 (수정)
    List<StepData> steps = [
      StepData(startTime: "2026-03-22T08:00:00", endTime: "2026-03-22T09:00:00", count: 500)
    ];

    //수면 데이터
    List<SleepData> sleeps = [
      SleepData(startTime: "2026-03-21T23:00:00", endTime: "2026-03-22T07:00:00")
    ];

    //스크린 타임 (app_usage 패키지 추가해야)
    List<ScreenTimeData> screenTimes = [
      ScreenTimeData(
          packageName: "com.instagram.android",
          totalTimeInForeground: 1800,
          sessionStart: "2026-03-22T10:00:00",
          sessionEnd: "2026-03-22T10:30:00"
      )
    ];

    // 알림 기록 읽기로 전환!!
    List<TransactionData> transactions = []; // 일단 빈 배열로 방어

    //최종 묶음
    return LifelogBatchRequest(
      runAt: runAt,
      location: location,
      steps: steps,
      sleeps: sleeps,
      screenTimes: screenTimes,
      transactions: transactions,
    );
  }
}