# 프로젝트 개요
MemorySeed는 안드로이드 기반의 라이프로그 서비스입니다.

- 앱은 라이프로그 데이터(걸음 수, 수면 시간, 화면 사용 시간, 거래 알림, 공부/작업 시간)를 수집하여 매일 서버에 업로드합니다.

- 서버는 PostgreSQL에 데이터를 저장하며, AccuWeather(서버 측 호출)를 통해 날씨 정보를 추가할 수 있습니다.

- 향후 주간/월간 데이터를 AI에 입력하여 인사이트를 도출하고 퀘스트를 추천할 예정입니다.

- 동기 부여 루프: 코인 획득 → 상점 구매 → 펫 커스터마이징

## 기술 스택
- Spring Boot + Spring MVC
- JPA(Hibernate) + PostgreSQL (Docker)
- 유효성 검사: jakarta.validation
- 사용자 인증: OAuth/JWT
- 배포: aws
