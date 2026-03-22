import 'package:flutter/material.dart';
 //공부 화면에서 허용앱 선택을 위해 있는 파일.
//추후 기기에 설치된 앱 목록을 가져오는 식으로 수정해야함.
class AppSelectScreen extends StatelessWidget {
  final List<String?> selectedApps;
  final int index;

  const AppSelectScreen({
    super.key,
    required this.selectedApps,
    required this.index,
  });

  @override
  Widget build(BuildContext context) {
    final apps = [
      'YouTube',
      'Kakao',
      'Chrome',
      'Instagram',
      'Music',
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('허용 앱 선택'),
      ),
      body: ListView.builder(
        itemCount: apps.length,
        itemBuilder: (context, i) {
          final app = apps[i];
          final alreadyUsed = selectedApps.contains(app);

          return ListTile(
            leading: const CircleAvatar(child: Icon(Icons.apps)),
            title: Text(app),
            trailing: alreadyUsed
                ? const Icon(Icons.check, color: Colors.grey)
                : null,
            enabled: !alreadyUsed,
            onTap: alreadyUsed
                ? null
                : () {
              Navigator.pop(context, app);
            },
          );
        },
      ),
    );
  }
}
