import 'package:flutter/material.dart';
import 'screens/main_screen.dart';
import 'managers/user_data_manager.dart';
import 'package:permission_handler/permission_handler.dart';

void main() async{
  WidgetsFlutterBinding.ensureInitialized();

  await requestAppPermissions();

  try {
    await UserDataManager.init();
  } catch (e) {
    print("초기화 에러: $e");
  }
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: MainScreen(),
    );
  }
}

Future<void> requestAppPermissions() async {
  Map<Permission, PermissionStatus> statuses = await [
    Permission.activityRecognition, // 걸음수
    Permission.sensors,             // 가속도 센서
    Permission.notification,        // 알림
  ].request();

  //로그확인용
  if (statuses[Permission.activityRecognition]!.isGranted) {
    print("권한 허용됨");
  } else {
    print("권한 거부됨");
  }
}