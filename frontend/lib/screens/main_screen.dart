import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'checklist.dart';
import 'shop_screen.dart';
import 'sleep_screen.dart';
import 'lock_screen.dart';
import 'my_page_screen.dart';
import 'dart:convert';
import '../models/time_block.dart';
import '../widgets/user_status_bar.dart'; // 상태바 위젯 import
import 'island_screen.dart';
import 'package:lifeseed/screens/debug_sync_screen.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  bool isSidebarOpen = false;
  late DateTime now;
  late final Timer clockTimer;

  List<TimeBlock> timeBlocks = [];

  @override
  void initState() {
    super.initState();
    now = DateTime.now();
    _loadTimeBlocks();

    clockTimer = Timer.periodic(
      const Duration(seconds: 30),
          (_) {
        setState(() {
          now = DateTime.now();
        });
      },
    );
  }

  // SharedPreferences타임라인 데이터 읽음
  Future<void> _loadTimeBlocks() async {
    final prefs = await SharedPreferences.getInstance();
    final List<String> storedList = prefs.getStringList('time_blocks') ?? [];

    final now = DateTime.now();

    setState(() {
      timeBlocks = storedList
          .map((item) => TimeBlock.fromMap(jsonDecode(item)))
          .where((block) =>
      block.start.year == now.year &&
          block.start.month == now.month &&
          block.start.day == now.day) // 오늘 날짜만 필터링
          .toList();
    });
  }

  //시간을 타임라인 위치(0.0 ~ 1.0)로 변환
  double _calculateProgress(DateTime time) {
    const int startHour = 6;
    int currentSeconds = time.hour * 3600 + time.minute * 60 + time.second;
    int startSeconds = startHour * 3600;
    int elapsedSeconds = currentSeconds - startSeconds;
    if (elapsedSeconds < 0) elapsedSeconds += 24 * 3600;
    return elapsedSeconds / (24 * 3600);
  }

  @override
  void dispose() {
    clockTimer.cancel();
    super.dispose();
  }

  double get dayProgress {
    const int startHour = 6;
    final int currentSeconds = now.hour * 3600 + now.minute * 60 + now.second;
    final int startSeconds = startHour * 3600;
    const int totalSecondsInDay = 24 * 60 * 60;

    int elapsedSeconds = currentSeconds - startSeconds;
    if (elapsedSeconds < 0) {
      elapsedSeconds += totalSecondsInDay;
    }
    return elapsedSeconds / totalSecondsInDay;
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;

    return Scaffold(
      backgroundColor: const Color(0xFFF6F1E8),
      body: GestureDetector(
        onHorizontalDragEnd: (details) {
          if (details.primaryVelocity == null) return;
          setState(() {
            isSidebarOpen = details.primaryVelocity! > 0;
          });
        },
        child: Stack(
          children: [
            // 메인 화면 영역
            SafeArea(
              child: Row(
                children: [
                  // 왼쪽 바
                  Container(
                    width: 60,
                    color: Colors.white,
                    child: Column(
                      children: [
                        const SizedBox(height: 16),
                        InkWell(
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (_) => const MyPageScreen()),
                            );
                          },
                          child: const CircleAvatar(radius: 20),
                        ),
                        const SizedBox(height: 16),
                        Expanded(
                          child: Align(
                            alignment: Alignment.topCenter,
                            child: LayoutBuilder(
                              builder: (context, constraints) {
                                return Stack(
                                  children: [
                                    Positioned(
                                      top:0,
                                      right:0,
                                      child: SafeArea(
                                          child: Padding(
                                            padding: const EdgeInsets.only(top:16,right:16),
                                            child: const UserStatusBar(),
                                          )
                                      )
                                    ),
                                  ],
                                );
                              },
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  // 중앙 메인
                  Expanded(
                    child: Stack(
                      children: [
                        Positioned(
                          top: 16,
                          right: 16,
                          child: const UserStatusBar(),
                        ),

                        // 캐릭터 표시 영역
                        Center(
                          child: Container(
                            height: 240,
                            width: 240,
                            decoration: BoxDecoration(
                              color: Colors.grey.shade300,
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: const Center(child: Text('CHARACTER')),
                          ),
                        ),

                        // 하단 컨트롤 패널
                        Positioned(
                          bottom: 16,
                          left: 16,
                          right: 16,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              IntrinsicWidth(
                                child: _buildActionBox([
                                  _buildIconButton(Icons.play_arrow, () async {
                                    await Navigator.push(context, MaterialPageRoute(builder: (_) => const LockScreen()));
                                    _loadTimeBlocks();
                                  }),
                                  const SizedBox(width: 12),
                                  _buildIconButton(Icons.nightlight_round, () async {
                                    await Navigator.push(context, MaterialPageRoute(builder: (_) => const DebugSyncScreen()));
                                    _loadTimeBlocks();
                                  }),
                                ]),
                              ),
                              const SizedBox(height: 12),
                              // 메뉴 박스(홈, 체크리스트, 상점)
                              Row(
                                mainAxisAlignment: MainAxisAlignment.end,
                                children: [
                                  IntrinsicWidth(
                                    child: _buildActionBox([
                                      const SizedBox(width: 12),
                                      _buildIconButton(Icons.home_rounded, () {
                                        Navigator.push(context, MaterialPageRoute(builder: (_) => const IslandScreen()));
                                      }),
                                      const SizedBox(width: 12),
                                      _buildIconButton(Icons.checklist, () {
                                        Navigator.push(context, MaterialPageRoute(builder: (_) => const ChecklistScreen()));
                                      }),
                                      const SizedBox(width: 12),
                                      _buildIconButton(Icons.storefront, () async {
                                        await Navigator.push(context, MaterialPageRoute(builder: (_) => const ShopScreen()));
                                      }),
                                    ]),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            // 슬라이드 사이드바 (타임라인)
            _buildSideBar(screenWidth),
          ],
        ),
      ),
    );
  }

  //위젯 분리함수

  Widget _buildActionBox(List<Widget> children) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 6)],
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: children),
    );
  }

  Widget _buildIconButton(IconData icon, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Icon(icon, size: 28),
    );
  }

  Widget _buildSideBar(double screenWidth) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeOut,
      width: isSidebarOpen ? screenWidth * 0.7 : 60,
      height: double.infinity,
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha : 0.1), blurRadius: 8)],
      ),
      child: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 10),
            InkWell(
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MyPageScreen())),
              child: const Center(child: CircleAvatar(radius: 20)),
            ),
            Expanded(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final timelineHeight = constraints.maxHeight * 0.9;
                  const double verticalPadding = 20.0;
                  return Center(
                    child: SizedBox(
                      height: timelineHeight + (verticalPadding * 2),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          // 시간 숫자 열
                          AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            width: isSidebarOpen ? 45 : 0,
                            child: isSidebarOpen ? _buildTimeLabels(timelineHeight, verticalPadding) : const SizedBox.shrink(),
                          ),
                          // 타임라인 바
                          _buildTimelineBar(timelineHeight, verticalPadding),
                          if (isSidebarOpen) const SizedBox(width: 45),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimeLabels(double height, double padding) {
    return Stack(
      children: [
        for (int i = 0; i <= 24; i += 3)
          Positioned(
            top: (height * (i / 24)) + padding - 7,
            right: 10,
            child: Text(
              ((i + 6) % 24).toString().padLeft(2, '0'),
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey.shade600),
            ),
          ),
      ],
    );
  }

  Widget _buildTimelineBar(double height, double padding) {
    return SizedBox(
      width: 14,
      child: Padding(
        padding: EdgeInsets.symmetric(vertical: padding),
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Container(
              width: 14,
              height: height,
              decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(7)),
            ),
            // 저장된 세션 표시
            for (var block in timeBlocks)
              Positioned(
                top: height * _calculateProgress(block.start),
                child: Container(
                  width: 14,
                  height: (height * _calculateProgress(block.end)) - (height * _calculateProgress(block.start)),
                  decoration: BoxDecoration(
                    color: block.type == 'study' ? Colors.orange.withValues(alpha : 0.7) : Colors.blue.withValues(alpha : 0.7),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
            // 눈금 및 현재 시간 선
            for (int i = 0; i <= 24; i++)
              Positioned(top: height * (i / 24), child: Container(width: 14, height: 2, color: Colors.grey.shade400)),
            Positioned(
              top: height * dayProgress,
              left: -2,
              child: Container(width: 18, height: 3, color: Colors.red),
            ),
          ],
        ),
      ),
    );
  }
}