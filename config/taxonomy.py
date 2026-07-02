"""카테고리 택소노미 (정본). slug = 정본 키, 표시명/하위토픽은 프롬프트·렌더용."""

# slug -> (표시명, [하위 토픽 예시])
CATEGORIES = {
    "ds_algo":       ("자료구조/알고리즘", ["해시", "트리", "정렬", "시간복잡도", "그래프 탐색"]),
    "network":       ("네트워크",         ["TCP/IP", "HTTP(S)", "로드밸런싱", "쿠키/세션", "CORS"]),
    "os":            ("운영체제",         ["프로세스/스레드", "동기화", "메모리", "스케줄링"]),
    "database":      ("데이터베이스",     ["정규화", "인덱스", "트랜잭션/격리수준", "락"]),
    "java":          ("언어/런타임(Java)", ["JVM", "GC", "컬렉션", "동시성"]),
    "spring":        ("프레임워크(Spring)", ["DI/IoC", "AOP", "트랜잭션", "JPA"]),
    "infra":         ("인프라/배포",      ["Docker", "CI/CD", "클라우드 기초", "모니터링"]),
    "server_ops":    ("서버 운영/명령어",  ["시스템 모니터링(top/uptime)", "메모리·디스크(free/df/du)",
                                          "네트워크(ss/curl/dig)", "systemd 서비스", "로그(journalctl/tail)",
                                          "원격·전송(ssh/rsync)", "cron 자동화", "컨테이너(docker)"]),
}

# 정본 slug 목록
SLUGS = list(CATEGORIES.keys())

# 출제 가중치. slug -> weight.
# 현재는 서버 운영/명령어 학습에만 집중하도록 server_ops만 출제(사용자 요청).
# _weighted_choice는 이 dict의 키 중에서만 고르므로, 여기 없는 카테고리는 출제되지 않는다.
# 다시 균등 랜덤으로 되돌리려면: CATEGORY_WEIGHTS = {slug: 1.0 for slug in SLUGS}
CATEGORY_WEIGHTS = {"server_ops": 1.0}

# 난이도 단계 (정본 표기)
DIFFICULTIES = ["기초", "중급", "심화"]


def display_name(slug: str) -> str:
    return CATEGORIES[slug][0]


def subtopics(slug: str) -> list[str]:
    return CATEGORIES[slug][1]
