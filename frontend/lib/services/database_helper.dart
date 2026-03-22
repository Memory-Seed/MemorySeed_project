import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
//서버로 보내기 전 기기 내부 SQLite DB에 저장
class DatabaseHelper {
  static final DatabaseHelper _instance = DatabaseHelper._internal();
  static Database? _database;

  factory DatabaseHelper() => _instance;
  DatabaseHelper._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    String path = join(await getDatabasesPath(), 'lifeseed_log.db');
    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    //steps
    await db.execute('''
      CREATE TABLE steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startTime TEXT,
        endTime TEXT,
        count INTEGER
      )
    ''');

    //sleeps
    await db.execute('''
      CREATE TABLE sleeps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startTime TEXT,
        endTime TEXT
      )
    ''');

    //screen_times
    await db.execute('''
      CREATE TABLE screen_times (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        packageName TEXT,
        totalTimeInForeground INTEGER,
        sessionStart TEXT,
        sessionEnd TEXT
      )
    ''');

    //알림(거래내역)
    await db.execute('''
      CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        amount INTEGER,
        transactionTime TEXT
      )
    ''');

    //위치
    //위치 정보는 배치 시점에 실시간으로 읽지만, 이력을 위해 생성)
    await db.execute('''
      CREATE TABLE locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lat REAL,
        lon REAL,
        recordedAt TEXT
      )
    ''');

    //타임블록
    await db.execute('''
      CREATE TABLE time_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        type TEXT, -- WORK, SLEEP, PLAY 등
        startTime TEXT,
        endTime TEXT
      )
    ''');
  }

  //데이터 삽입 함수 예시
  Future<int> insertStep(Map<String, dynamic> row) async {
    Database db = await database;
    return await db.insert('steps', row);
  }

  //배치 전송용 걸음수 조회
  Future<List<Map<String, dynamic>>> getAllSteps() async {
    Database db = await database;
    return await db.query('steps');
  }

  //전송 완료 후 테이블 비움
  Future<void> clearSteps() async {
    Database db = await database;
    await db.delete('steps');
  }
}