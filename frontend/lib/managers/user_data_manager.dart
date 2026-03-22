import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:lifeseed/services/api_service.dart';
//사용자의 자산, 데이터 중앙 관리 + 서버와 동기화

class UserDataManager {
  // 관찰 가능 변수
  static final ValueNotifier<int> userCoins = ValueNotifier<int>(0);
  static final ValueNotifier<int> userHearts = ValueNotifier<int>(0);

  // 라이프로그 기록 데이터
  static final ValueNotifier<int> todayStudyMinutes = ValueNotifier<int>(0);
  static final ValueNotifier<double> todaySleepHours = ValueNotifier<double>(0.0);
  static final ValueNotifier<int> weeklyStudyMinutes = ValueNotifier<int>(0);

  // 1. 초기화 및 서버 데이터 동기화
  static Future<void> init() async {
    await syncWithServer();
  }

  // 2. 서버 잔액과 앱 데이터 동기화 (핵심!)
  static Future<void> syncWithServer() async {
    try {
      // ApiService를 사용하여 최신 프로필 정보 획득
      final profileData = await ApiService().getUserProfile();

      // 서버의 실제 데이터로 ValueNotifier 갱신
      userCoins.value = profileData['coin'] ?? profileData['priceCoin'] ?? 0;
      userHearts.value = profileData['hearts'] ?? 0;

      // 로컬 SharedPreferences에 백업 (오프라인 대비)
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt('user_coins', userCoins.value);
      await prefs.setInt('user_hearts', userHearts.value);

      print("✅ 서버 데이터 동기화 성공: 코인 ${userCoins.value}");
    } catch (e) {
      print("⚠️ 서버 동기화 실패, 로컬 데이터를 불러옵니다.");
      final prefs = await SharedPreferences.getInstance();
      userCoins.value = prefs.getInt('user_coins') ?? 0;
      userHearts.value = prefs.getInt('user_hearts') ?? 0;
    }
  }

  // 3. 공부 시간 기록 (로컬 저장 예시)
  static Future<void> addStudyTime(int minutes) async {
    todayStudyMinutes.value += minutes;
    weeklyStudyMinutes.value += minutes;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('today_study', todayStudyMinutes.value);
  }

  // 수동 업데이트가 필요한 경우 ?
  static Future<void> updateCoinsLocally(int amount) async {
    userCoins.value += amount;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('user_coins', userCoins.value);
  }
}