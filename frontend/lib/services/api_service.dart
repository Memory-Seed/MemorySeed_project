import 'package:dio/dio.dart';
import 'package:lifeseed/models/lifelog_batch.dart';
import 'package:lifeseed/models/checklist_item.dart';
//서버 통신 관련
class ApiService {
  static const String baseUrl = "http://10.0.2.2:8080";

  final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    headers: {
      'X-USER-ID': '1', //임시 인증!
      'Content-Type': 'application/json',
    },
  ));

  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  Dio get dio => _dio;

  //유저 프로필 조회
  Future<Map<String, dynamic>> getUserProfile() async {
    try {
      final response = await _dio.get('/api/user/profile'); //?
      if (response.statusCode == 200) {
        return response.data;
      } else {
        throw Exception("서버 응답 에러");
      }
    } catch (e) {
      print("에러: $e");
      rethrow;
    }
  }

  //상점 아이템 조회
  Future<List<dynamic>> getShopItems() async {
    try {
      final response = await _dio.get('/api/shop/items');
      if (response.statusCode == 200) {
        return response.data as List<dynamic>;
      }
      return [];
    } catch (e) {
      print("조회 실패: $e");
      return [];
    }
  }

  //아이템 구매
  Future<bool> purchaseItem(String itemCode) async {
    try {
      final response = await _dio.post(
        '/api/shop/purchase',
        data: {'itemCode': itemCode},
      );
      return response.statusCode == 200;
    } catch (e) {
      print("구매 실패: $e");
      return false; // false 처리
    }
  }

  //라이프로그 배치 전송
  Future<int?> sendLifelogBatch(LifelogBatchRequest request) async {
    try {
      final response = await _dio.post(
        '/api/lifelog/batch',
        data: request.toJson(),
      );

      if (response.statusCode == 200) {
        print("성공 runId: ${response.data['runId']}");
        return response.data['runId'];
      }
      return null;
    } catch (e) {
      print("실패: $e");
      return null;
    }
  }
  // 진행 중인 퀘스트 목록
  Future<List<ChecklistItem>> getActiveQuests() async {
    try {
      final response = await _dio.get('/api/quests/active');
      final List<dynamic> data = response.data;
      return data.map((json) => ChecklistItem.fromJson(json)).toList();
    } catch (e) {
      print("실패: $e");
      return [];
    }
  }

// 커스텀 퀘스트 생성
  Future<ChecklistItem?> createCustomQuest(String title, int targetValue) async {
    try {
      final response = await _dio.post('/api/quests/custom', data: {
        "title": title,
        "description": "", // 필요시 추가
        "category": "ETC",
        "dueDate": DateTime.now().toIso8601String().split('T')[0], // YYYY-MM-DD
        "targetValue": targetValue
      });
      return ChecklistItem.fromJson(response.data);
    } catch (e) {
      print("퀘스트 생성 실패: $e");
      return null;
    }
  }

// 퀘스트 완료
  Future<bool> completeQuest(int id) async {
    try {
      final response = await _dio.patch('/api/quests/$id/complete');
      return response.statusCode == 200;
    } catch (e) {
      print("퀘스트 완료 처리 실패: $e");
      return false;
    }
  }

  // 펫 정보 조회
  Future<Map<String, dynamic>> getPetInfo() async {
    final response = await _dio.get('/api/quests/pet'); //?
    return response.data;
  }

// 펫 꾸미기 PUT /api/pet/customization
  Future<Map<String, dynamic>> updatePetCustomization(Map<String, String?> items) async {
    final response = await _dio.put('/api/pet/customization', data: items);
    return response.data;
  }

}

