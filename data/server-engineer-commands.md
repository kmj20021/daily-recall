# 서버 엔지니어 실무 명령어 정리

> 판단 기준: 최신 실무 블로그(2025~2026) + 사용 빈도 통계(Stack Overflow 2025, CNCF 2025, LinuxBlog.io 2026 등)를 교차해, **"현장에서 실제로 자주 치는 것"** 위주로 정리.
>
> 핵심 원칙 두 가지
> 1. 목록을 다 외우지 말 것 — 명령어 100개보다 자주 쓰는 것의 **플래그**를 깊게. (선임 admin은 `ls`를 하루 50번, `strace`는 1년에 두 번 쓴다)
> 2. 유창함은 읽어서가 아니라 **수십 번 직접 쳐봐서** 생긴다. 1~6번부터 손에 익힐 것.

---

## 우선순위 가이드

| 단계 | 영역 | 이유 |
|------|------|------|
| **먼저** | 1~6 (모니터링·메모리·디스크·네트워크·서비스·로그) | "서버 느려요/죽었어요" 트러블슈팅의 핵심. 면접 단골. |
| 그다음 | 7~11 (파일·원격·자동화·컨테이너·권한) | 작업하면서 자연스럽게 손에 붙음. |
| 나중에 | strace, perf, tcpdump 등 특수 도구 | 상황이 요구할 때 익히면 됨. |

---

## 1. 시스템 모니터링 (CPU·부하)

| 명령어 | 용도 | 메모 |
|--------|------|------|
| `top` / `htop` | 실시간 프로세스·자원 확인 | `htop`이 더 편함(색상·트리·대화형). 요즘은 `btop`도 인기 |
| `uptime` | 가동시간 + 접속자 수 + 부하 평균 | load average 3개 = 1·5·15분 평균. 코어 수보다 높으면 과부하 |
| `w` | 로그인 사용자 + 프로세스 + 부하 | 누가 뭘 하고 있나 한눈에 |
| `ps aux` | 전체 프로세스 스냅샷 | 보통 `ps aux \| grep <이름>`으로 특정 추적 |

```bash
htop                      # 대화형 모니터링
uptime                    # 0.00, 0.03, 0.22 ← 1/5/15분 부하
ps aux | grep nginx       # nginx 프로세스 찾기
```

---

## 2. 메모리

| 명령어 | 용도 | 메모 |
|--------|------|------|
| `free -h` | 메모리·스왑 잔량 | `-h` = 사람이 읽기 좋은 단위(GB 등) |
| `vmstat 1` | 1초 간격 메모리·스왑·IO 추이 | 스왑이 계속 일어나면 메모리 부족 신호 |

```bash
free -h
vmstat 1                  # Ctrl+C로 종료
```

---

## 3. 디스크 / 스토리지

| 명령어 | 용도 | 메모 |
|--------|------|------|
| `df -h` | 디스크 잔량 | "디스크 꽉 참" 장애의 1번 명령어 |
| `du -sh *` | 현재 폴더 용량 범인 찾기 | 어디가 용량을 먹는지 추적 |
| `iostat -x 1` | 디스크 IO 부하 | sysstat 패키지. I/O 병목 추적 |

```bash
df -h                     # 전체 파티션 잔량
du -sh *                  # 현재 디렉터리 항목별 용량
du -sh /var/log           # 특정 경로 용량
```

---

## 4. 네트워크 (서버 엔지니어 핵심)

| 명령어 | 용도 | 메모 |
|--------|------|------|
| `ip a` | 인터페이스·IP 확인 | 예전 `ifconfig` 대체 |
| `ss -tuln` | 열린 포트·리스닝 서비스 | 예전 `netstat` 대체. "뭐가 듣고 있나" 확인 |
| `curl -I <주소>` | 엔드포인트·연결 테스트 | 헤더만 받아 응답 확인 |
| `ping` | 기본 연결 확인 | 도달 가능 여부 |
| `nc` (netcat) | 포트 열림·도달 확인 | "네트워킹의 맥가이버 칼" |
| `dig` / `nslookup` | DNS 조회 | 이름 해석 문제 추적 |
| `tcpdump` | 패킷 캡처 | 고급. 상황 될 때 |

```bash
ip a                      # 내 IP/인터페이스
ss -tuln                  # 리스닝 중인 포트 전체
curl -I https://example.com
nc -zv 192.168.1.10 22    # 원격 22번 포트 열렸나
dig example.com
```

---

## 5. 서비스 관리 (systemd)

> systemd 전환으로 `systemctl`이 현대 리눅스에서 **가장 많이 쓰는 관리 명령**. 매일 씀.

| 명령어 | 용도 |
|--------|------|
| `systemctl status <서비스>` | 상태 확인 |
| `systemctl start/stop/restart <서비스>` | 시작/정지/재시작 |
| `systemctl enable/disable <서비스>` | 부팅 시 자동시작 on/off |

```bash
systemctl status nginx
sudo systemctl restart nginx
sudo systemctl enable nginx     # 부팅 시 자동 시작
```

---

## 6. 로그 (트러블슈팅의 시작점)

> 뭔가 잘못되면 **로그가 첫 번째로 봐야 할 곳.**

| 명령어 | 용도 | 메모 |
|--------|------|------|
| `journalctl -u <서비스>` | systemd 서비스 로그 | `-f` 실시간, `--since` 기간 필터 |
| `tail -f <파일>` | 로그 실시간 추적 | 쌓이는 걸 보면서 디버깅 |
| `grep` | 패턴 검색 | `awk`·`sed`와 묶어 트리오로 자주 씀 |

```bash
journalctl -u nginx -f          # nginx 로그 실시간
journalctl -u nginx --since "10 min ago"
tail -f /var/log/nginx/error.log
grep -i error /var/log/syslog   # 대소문자 무시하고 error 검색
```

---

## 7. 파일 관리 / 탐색

**생존 키트**: `ls` `cd` `cp` `mv` `rm` `grep` `find` `top` `df` `tail`

| 명령어 | 용도 | 메모 |
|--------|------|------|
| `ls -lah` | 상세 목록 | 플래그가 명령어 100개보다 유용 |
| `find` | 조건 검색 | 이름·크기·시간 등으로 찾기 |
| `chmod` / `chown` | 권한 / 소유자 변경 | |
| `ln -s` | 심볼릭 링크 | |

```bash
ls -lah                         # 숨김파일+사람이읽는크기+상세
find /var/log -name "*.log"     # .log 파일 찾기
find / -size +100M              # 100MB 넘는 파일
chmod 644 file.txt
chown user:group file.txt
```

---

## 8. 원격 접속 / 파일 전송

| 명령어 | 용도 | 메모 |
|--------|------|------|
| `ssh` | 원격 서버 접속 | 서버 엔지니어의 출퇴근길 |
| `scp` | 파일 전송 | 통째로 복사 |
| `rsync` | 동기화 전송 | **변경분만** 전송 → 빠르고 대역폭 절약. 백업·동기화에 선호 |

```bash
ssh user@192.168.1.10
scp file.txt user@host:/backup/
rsync -avz /data/ user@host:/backup/   # 증분 동기화
```

---

## 9. 예약 작업 / 자동화

| 명령어 | 용도 |
|--------|------|
| `crontab -e` | 예약 작업 편집 (백업·로그 로테이션·리포트 등) |

```bash
crontab -e
# ┌ 분(0-59) ┌ 시(0-23) ┌ 일(1-31) ┌ 월(1-12) ┌ 요일(0-7, 일=0/7)
# *          *          *          *          *   실행할-명령
# 예) 매일 새벽 3시 백업:
# 0 3 * * * /home/user/backup.sh
```

---

## 10. 컨테이너 (이제 기본기)

> Docker 71% 채택률로 `ls`·`grep`과 나란히 일상 명령에 진입. 리눅스가 Docker 배포의 75%를 차지.

| 명령어 | 용도 |
|--------|------|
| `docker ps` | 실행 중 컨테이너 목록 (`-a`로 정지된 것까지) |
| `docker logs <컨테이너>` | 컨테이너 로그 |
| `docker exec -it <컨테이너> bash` | 컨테이너 안으로 진입 |
| `docker images` | 이미지 목록 |

```bash
docker ps -a
docker logs -f my-container
docker exec -it my-container bash
```

---

## 11. 권한 상승

| 명령어 | 용도 |
|--------|------|
| `sudo` | 거의 모든 관리 작업의 접두사 |

```bash
sudo systemctl restart nginx
sudo journalctl -u nginx
```

---

## 트러블슈팅 사고 흐름 (면접 답변용)

> "서버가 느려요/죽었어요" → 어디부터 보나? 이 순서가 입에서 나오면 면접 통과.

```
1. 부하 확인      → uptime / top(htop)      "부하 평균이 코어 수보다 높나?"
2. 자원 범인 찾기  → top → CPU냐 메모리냐
       ├ CPU      → top에서 점유 프로세스 확인
       ├ 메모리   → free -h (스왑 일어나나)
       └ 디스크   → df -h (꽉 찼나) → du로 추적
3. 네트워크 확인   → ss -tuln (포트 열렸나) / curl (응답 오나)
4. 서비스 상태    → systemctl status <서비스>
5. 로그 추적      → journalctl -u <서비스> / tail -f
```

---

## 학습 메모

- **플래그부터**: `ls`보다 `ls -lah`. 자주 쓰는 명령의 옵션을 깊게.
- **실습으로**: 일부러 고장 내고 → 명령어로 추적 → 고치기. 한 사이클이 곧 면접 경험.
- **레퍼런스**: `man <명령어>`로 전체 매뉴얼, `tldr <명령어>`로 자주 쓰는 패턴만.
