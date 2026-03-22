import 'package:flutter/material.dart';
import 'main_screen.dart';
import 'package:lifeseed/widgets/user_status_bar.dart';

class IslandScreen extends StatefulWidget {
  const IslandScreen({super.key});

  @override
  State<IslandScreen> createState() => _IslandScreenState();
}

class _IslandScreenState extends State<IslandScreen> {
  bool isDetailMode = false;
  late PageController _pageController;
  int currentIndex = 0;

  final List<Map<String, dynamic>> islands = [
    {'name': '섬 1', 'color': '0xFF81C784', 'report': {'time': '02:45', 'rate': '85%', 'coin': '+120'}},
    {'name': '섬 2', 'color': '0xFF64B5F6', 'report': {'time': '01:20', 'rate': '40%', 'coin': '+45'}},
    {'name': '섬 3', 'color': '0xFFFFB74D', 'report': {'time': '04:10', 'rate': '100%', 'coin': '+300'}},
    {'name': '섬 4', 'color': '0xFFBA68C8', 'report': {'time': '00:00', 'rate': '0%', 'coin': '+0'}},
  ];

  @override
  void initState() {
    super.initState();
    _pageController = PageController(initialPage: currentIndex);
  }

  Alignment _getZigzagAlignment(int index) {
    switch (index) {
      case 0: return const Alignment(-0.6, -0.8);
      case 1: return const Alignment(0.6, -0.25);
      case 2: return const Alignment(-0.6, 0.3);
      case 3: return const Alignment(0.6, 0.85);
      default: return Alignment.center;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE0F2F1),
      resizeToAvoidBottomInset: false,
      body: SafeArea(
        child: Stack(
          children: [
            //전체 지도
            AnimatedOpacity(
              duration: const Duration(milliseconds: 400),
              opacity: isDetailMode ? 0.2 : 1.0,
              child: _buildFullMapView(),
            ),

            //상세 페이지 (확대 상태 + 하단 리포트)
            if (isDetailMode) _buildDetailPageView(),

            //상단 상태바
            Positioned(
              top: 16,
              right: 16,
              child: const UserStatusBar(),
            ),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomBar(),
    );
  }

  Widget _buildFullMapView() {
    return Stack(
      children: [
        for (int i = 0; i < islands.length; i++)
          Align(
            alignment: _getZigzagAlignment(i),
            child: GestureDetector(
              onTap: () {
                setState(() {
                  currentIndex = i;
                  _pageController = PageController(initialPage: i);
                  isDetailMode = true;
                });
              },
              child: _buildIslandWidget(i, isSmall: true),
            ),
          ),
      ],
    );
  }

  //상세 보기(섬은 중앙, 리포트는 최하단) ---
  Widget _buildDetailPageView() {
    return Container(
      color: Colors.black.withOpacity(0.3),
      child: PageView.builder(
        controller: _pageController,
        itemCount: islands.length,
        onPageChanged: (index) => setState(() => currentIndex = index),
        itemBuilder: (context, index) {
          return GestureDetector(
            onTap: () => setState(() => isDetailMode = false),
            behavior: HitTestBehavior.opaque,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 40.0),
              child: Column(
                children: [
                  const Spacer(), // 섬을 중앙으로 밀어내기 위함
                  _buildIslandWidget(index, isSmall: false),
                  const SizedBox(height: 20),
                  Text(
                    islands[index]['name']!,
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      shadows: [Shadow(color: Colors.black45, blurRadius: 10)],
                    ),
                  ),
                  const Spacer(), //섬과 리포트 사이 공간

                  //일일 리포트 카드 (화면 하단)
                  _buildDailyReportCard(index),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildIslandWidget(int index, {required bool isSmall}) {
    return Hero(
      tag: 'island_$index',
      createRectTween: (begin, end) => MaterialRectCenterArcTween(begin: begin, end: end),
      child: Container(
        width: isSmall ? 120 : 280,
        height: isSmall ? 120 : 280,
        decoration: BoxDecoration(
          color: Color(int.parse(islands[index]['color']!)),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: isSmall ? 10 : 30),
          ],
        ),
        child: Center(
          child: Icon(
            Icons.terrain_rounded,
            size: isSmall ? 50 : 120,
            color: Colors.white.withOpacity(0.7),
          ),
        ),
      ),
    );
  }

  Widget _buildDailyReportCard(int index) {
    final report = islands[index]['report'];
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 30),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.9),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildReportItem("집중", report['time']),
          _buildReportItem("달성", report['rate']),
          _buildReportItem("코인", report['coin']),
        ],
      ),
    );
  }

  Widget _buildReportItem(String label, String value) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey)),
        Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
      ],
    );
  }

  // 하단
  Widget _buildBottomBar() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.only(right: 16, bottom: 10),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 8)],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: const Icon(Icons.home_rounded, size: 28),
                    onPressed: () => Navigator.pushReplacement(
                      context, MaterialPageRoute(builder: (_) => const MainScreen()),
                    ),
                  ),
                  const SizedBox(height: 24, child: VerticalDivider(width: 10)),
                  IconButton(
                    icon: const Icon(Icons.assessment_rounded, size: 28),
                    onPressed: () => _showWeeklyReport(context),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showWeeklyReport(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("주간 리포트"),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text("닫기"))],
      ),
    );
  }
}