import 'package:flutter/material.dart';
import '../models/shop_item.dart';
import '../services/api_service.dart';
import '../managers/user_data_manager.dart';
import '../widgets/shop_item_tile.dart';
import '../widgets/user_status_bar.dart';
import 'shop_detail_screen.dart';

class ShopScreen extends StatefulWidget {
  const ShopScreen({super.key});

  @override
  State<ShopScreen> createState() => _ShopScreenState();
}

class _ShopScreenState extends State<ShopScreen> {
  // 카테고리 정의
  final List<String> categories = ['TOP', 'HAT', 'OUTER', 'FURNITURE'];
  int selectedCategoryIndex = 0;

  List<ShopItem> items = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchShopItems();
  }

  //상점 아이템 목록 조회
  Future<void> _fetchShopItems() async {
    setState(() => _isLoading = true);
    try {
      final List<dynamic> data = await ApiService().getShopItems();

      setState(() {
        items = data.map((e) => ShopItem.fromJson(e)).toList();
        _isLoading = false;
      });
    } catch (e) {
      debugPrint("상점 목록 로딩 에러: $e");
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("아이템 목록을 가져오지 못했습니다.")),
        );
      }
    }
  }

  //API: 아이템 구매 및 서버 동기화
  Future<void> _purchaseItem(ShopItem item) async {
    try {
      //구매 요청
      bool isSuccess = await ApiService().purchaseItem(item.code);

      if (isSuccess) {
        // 구매 성공 시 최신 코인 정보 서버에서 다시 가져옴
        await UserDataManager.syncWithServer();

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('${item.name} 구매 완료!')),
          );
          //새로고침 (구매 완료 표시 해야해서)
          _fetchShopItems();
          Navigator.pop(context); //닫기
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("코인이 부족하거나 이미 소유한 아이템입니다.")),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("구매 처리 중 오류가 발생했습니다.")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // 카테고리별 아이템 필터링
    final filteredItems = items
        .where((e) => e.category == categories[selectedCategoryIndex])
        .toList();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Align(
          alignment: Alignment.centerRight,
          child: UserStatusBar(),
        ),
      ),
      body: Column(
        children: [
          // 탭 바 영역
          _buildCategoryTabs(),
          const Divider(height: 1),

          // 리스트 영역
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : filteredItems.isEmpty
                ? const Center(child: Text("해당 카테고리에 아이템이 없습니다."))
                : ListView.builder(
              itemCount: filteredItems.length,
              padding: const EdgeInsets.symmetric(vertical: 10),
              itemBuilder: (context, i) {
                final item = filteredItems[i];
                return ListTile(
                  leading: Image.asset(
                      item.assetKey,
                      width: 50,
                      errorBuilder: (_, __, ___) => const Icon(Icons.inventory_2)
                  ),
                  title: Text(item.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('${item.priceCoin} 코인'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => ShopDetailScreen(
                          item: item,
                          onBuy: () => _purchaseItem(item),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  // 카테고리 탭 빌더
  Widget _buildCategoryTabs() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: List.generate(categories.length, (i) {
          final isSelected = i == selectedCategoryIndex;
          return InkWell(
            onTap: () => setState(() => selectedCategoryIndex = i),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
              decoration: BoxDecoration(
                border: Border(
                  bottom: BorderSide(
                    color: isSelected ? Colors.blue : Colors.transparent,
                    width: 2,
                  ),
                ),
              ),
              child: Text(
                categories[i],
                style: TextStyle(
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  color: isSelected ? Colors.blue : Colors.grey,
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}