# Oracle Cloud + Hermes Agent — 처음부터 베포 가이드

> 새 프로젝트에서 똑같이 배포할 때 이 문서만 보고 따라가면 됨.
> 기준: 37_BA(ClickAround)에서 검증된 스택 (2026-04-26).
> 실제 운영 인스턴스 정보는 `ORACLE_DEPLOYMENT.md` 참고.

---

## 0. 전체 그림 (5단계, 약 90분 소요)

```
1. Oracle Cloud 계정 + OCI CLI       (15분, 1회만)
2. VM 프로비저닝 (VCN/Subnet/VM)     (10분)
3. VM 부트스트랩 (OS, nginx, python) (15분)
4. Hermes Agent 설치 + 설정          (30분)
5. 첫 크론 실행 검증                  (10분)
```

목표: VM 1대 위에 자율 AI 에이전트가 24/7 cron으로 컨텐츠/포스트/리포트 생산.

---

## 1. Oracle Cloud 계정 + OCI CLI

### 1.1 계정 생성
- https://cloud.oracle.com/ 가입
- **카드 등록 필수** (Always Free Tier는 무과금이지만 인증용)
- 메일 인증 → Console 진입

### 1.2 OCI CLI 설치
```bash
# Windows (PowerShell or git-bash)
pip install oci-cli

# PATH 추가 (예시 경로, 본인 환경 맞게)
export PATH="$PATH:/c/Users/<user>/AppData/Roaming/Python/Python313/Scripts"

# 확인
oci --version
```

### 1.3 API Key 생성
```bash
mkdir -p ~/.oci
PASSPHRASE='<원하는-비밀번호>'  # 메모해 둘 것
openssl genrsa -aes128 -passout "pass:$PASSPHRASE" -out ~/.oci/oci_api_key.pem 2048
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -passin "pass:$PASSPHRASE" -out ~/.oci/oci_api_key_public.pem

# fingerprint (Oracle Console 등록 시 비교용)
openssl rsa -pubout -outform DER -in ~/.oci/oci_api_key.pem -passin "pass:$PASSPHRASE" 2>/dev/null \
  | openssl md5 -c | awk '{print $2}'
```

### 1.4 공개키 Console 등록
1. Profile (오른쪽 상단) → My profile
2. Tokens and keys → API keys → Add API key
3. **Paste a public key** → `~/.oci/oci_api_key_public.pem` 내용 붙여넣기
4. Add → 표시되는 config 정보 복사

### 1.5 `~/.oci/config` 작성
```ini
[DEFAULT]
user=ocid1.user.oc1..xxxxxxxxxx        # Console에서 복사
fingerprint=24:79:ec:d8:...            # 위 명령 결과
tenancy=ocid1.tenancy.oc1..xxxxxxxxxx  # Console에서 복사
region=ap-chuncheon-1                  # Korea (또는 본인 리전)
key_file=~/.oci/oci_api_key.pem
pass_phrase=<원하는-비밀번호>
```

### 1.6 연결 테스트
```bash
oci iam region list --output table
# 정상이면 리전 목록 표시
```

---

## 2. VM 프로비저닝

### 2.1 환경변수 설정
```bash
export TENANCY=ocid1.tenancy.oc1..xxxxxxxxxx  # 본인 tenancy
export SUPPRESS_LABEL_WARNING=True
```

### 2.2 VCN 생성
```bash
VCN=$(oci network vcn create --compartment-id $TENANCY \
  --cidr-blocks '["10.0.0.0/16"]' \
  --display-name "myproj-vcn" --dns-label "myprojvcn" \
  --query 'data.id' --raw-output)
echo "VCN=$VCN"
```

### 2.3 Internet Gateway
```bash
IGW=$(oci network internet-gateway create --compartment-id $TENANCY \
  --vcn-id $VCN --display-name "myproj-igw" --is-enabled true \
  --query 'data.id' --raw-output)
```

### 2.4 Route Table → Internet
```bash
RT_ID=$(oci network route-table list --compartment-id $TENANCY \
  --vcn-id $VCN --query 'data[0].id' --raw-output)
oci network route-table update --rt-id $RT_ID \
  --route-rules "[{\"cidrBlock\":\"0.0.0.0/0\",\"networkEntityId\":\"$IGW\"}]" --force
```

### 2.5 Security List (SSH + HTTP + HTTPS)
```bash
SL_ID=$(oci network security-list list --compartment-id $TENANCY \
  --vcn-id $VCN --query 'data[0].id' --raw-output)
oci network security-list update --security-list-id $SL_ID \
  --ingress-security-rules '[
    {"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":22,"max":22}}},
    {"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":80,"max":80}}},
    {"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":443,"max":443}}}
  ]' \
  --egress-security-rules '[{"destination":"0.0.0.0/0","protocol":"all"}]' --force
```

### 2.6 Public Subnet
```bash
AD=$(oci iam availability-domain list --compartment-id $TENANCY \
  --query 'data[0]."name"' --raw-output)
SUBNET=$(oci network subnet create --compartment-id $TENANCY \
  --vcn-id $VCN --cidr-block "10.0.0.0/24" \
  --display-name "myproj-public-subnet" --dns-label "myprojpub" \
  --availability-domain "$AD" --query 'data.id' --raw-output)
```

### 2.7 SSH Key
```bash
ssh-keygen -t rsa -b 2048 -f ~/.ssh/oracle_key_myproj -N ""
```

### 2.8 VM 인스턴스 — Shape 선택

| Shape | OCPU/RAM | 비용 | 권장 |
|-------|----------|------|------|
| **VM.Standard.A1.Flex** (ARM) | 4/24GB Always Free | $0 | ⭐ 신규 (재고 있으면) |
| **VM.Standard.E4.Flex** (AMD) | 1-2/4-8GB Always Free | $0 | 37_BA 검증 (재고 안정) |
| VM.Standard.E2.1.Micro (AMD) | 1/1GB Always Free | $0 | 너무 작음 비추 |

ARM A1 시도 (실패 시 E4 fallback):
```bash
# ARM A1 시도
IMAGE_ID=$(oci compute image list --compartment-id $TENANCY \
  --operating-system "Canonical Ubuntu" --operating-system-version "22.04" \
  --shape "VM.Standard.A1.Flex" --query 'data[0].id' --raw-output)

INSTANCE_ID=$(oci compute instance launch --compartment-id $TENANCY \
  --availability-domain "$AD" --shape "VM.Standard.A1.Flex" \
  --shape-config '{"ocpus":4,"memoryInGBs":24}' \
  --display-name "myproj-vm" --image-id "$IMAGE_ID" \
  --subnet-id "$SUBNET" --assign-public-ip true \
  --ssh-authorized-keys-file ~/.ssh/oracle_key_myproj.pub \
  --boot-volume-size-in-gbs 100 --query 'data.id' --raw-output 2>&1 || echo "ARM_FAILED")

# 실패 시 E4.Flex로
if [[ "$INSTANCE_ID" == *FAILED* ]] || [ -z "$INSTANCE_ID" ]; then
  IMAGE_ID=$(oci compute image list --compartment-id $TENANCY \
    --operating-system "Canonical Ubuntu" --operating-system-version "22.04" \
    --shape "VM.Standard.E4.Flex" --query 'data[0].id' --raw-output)
  INSTANCE_ID=$(oci compute instance launch --compartment-id $TENANCY \
    --availability-domain "$AD" --shape "VM.Standard.E4.Flex" \
    --shape-config '{"ocpus":2,"memoryInGBs":4}' \
    --display-name "myproj-vm" --image-id "$IMAGE_ID" \
    --subnet-id "$SUBNET" --assign-public-ip true \
    --ssh-authorized-keys-file ~/.ssh/oracle_key_myproj.pub \
    --boot-volume-size-in-gbs 50 --query 'data.id' --raw-output)
fi

echo "INSTANCE_ID=$INSTANCE_ID"
```

### 2.9 Public IP 확인 + SSH
```bash
VNIC_ID=$(oci compute vnic-attachment list --compartment-id $TENANCY \
  --instance-id $INSTANCE_ID --query 'data[0]."vnic-id"' --raw-output)
PUBLIC_IP=$(oci network vnic get --vnic-id $VNIC_ID --query 'data."public-ip"' --raw-output)
echo "PUBLIC_IP=$PUBLIC_IP"
ssh -i ~/.ssh/oracle_key_myproj ubuntu@$PUBLIC_IP "uname -a && uptime"
```

---

## 3. VM 부트스트랩 (OS 패키지)

SSH 접속 후 한번에 실행:

```bash
# system update
sudo apt-get update && sudo apt-get upgrade -y

# essentials
sudo apt-get install -y \
  python3 python3-pip python3-venv \
  nginx certbot python3-certbot-nginx \
  git curl jq zip unzip wkhtmltopdf \
  iptables-persistent netfilter-persistent

# nginx default site OK 확인
sudo systemctl enable nginx --now
curl -s -o /dev/null -w "nginx: http=%{http_code}\n" http://localhost/

# iptables 80/443 영구화 (재부팅 안전)
sudo iptables -I INPUT 5 -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

> ⚠️ **iptables 영구화 누락 시**: 재부팅 후 80/443 차단됨. 외부 접근 안 됨. 37_BA에서 한 번 당함.

### 3.1 사이트 디렉토리 (예시)
```bash
sudo mkdir -p /var/www/html/myproj/blog
sudo chown -R www-data:www-data /var/www/html/myproj
echo '<h1>hello</h1>' | sudo tee /var/www/html/myproj/index.html
curl -s http://localhost/myproj/
```

### 3.2 (선택) 도메인 + HTTPS
```bash
# 도메인 DNS A record → PUBLIC_IP 설정 후
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com \
  --email you@example.com --agree-tos --non-interactive
```

---

## 4. Hermes Agent 설치 + 설정

### 4.1 코드 클론
```bash
cd /home/ubuntu
git clone <hermes-agent-repo> hermes-business
# 또는 37_BA에서 D:/Data/37_BA/hermes-agent/ 통째로 scp

mkdir -p ~/.hermes/{cron,memory,skills,memory/company,memory/finance}
```

### 4.2 Python 의존성
```bash
cd /home/ubuntu/hermes-business/hermes-agent
pip3 install -r requirements.txt
# 또는 setup.py가 있으면
pip3 install -e .
```

### 4.3 환경 변수 (`~/.hermes/.env`)
필수 27개 키 (37_BA의 `D:/Data/37_BA/deploy/.env` 참고). 신규 프로젝트면 최소:

```bash
cat > /home/ubuntu/.hermes/.env <<'EOF'
# LLM
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxx
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1

# Oracle (위에서 만든 값)
OCI_TENANCY_OCID=ocid1.tenancy.oc1..xxx
OCI_USER_OCID=ocid1.user.oc1..xxx
OCI_REGION=ap-chuncheon-1
OCI_INSTANCE_ID=ocid1.instance.oc1.ap-chuncheon-1.xxx
OCI_VM_IP=<PUBLIC_IP>

# Telegram (옵션이지만 강추)
TELEGRAM_BOT_TOKEN=xxxxxxxxx:xxxx
TELEGRAM_CHAT_ID=<운영자-chat-id>
TELEGRAM_HOME_CHANNEL=<운영자-chat-id>
TELEGRAM_ALLOWED_USERS=<운영자-chat-id>

# 결제 (Lemon Squeezy)
LEMONSQUEEZY_API_KEY=eyJxx...
LEMONSQUEEZY_STORE_ID=300xxx

# 보안
TIRITH_ENABLED=false
GATEWAY_ALLOW_ALL_USERS=false
EOF
chmod 600 /home/ubuntu/.hermes/.env
```

### 4.4 config.yaml
```yaml
# /home/ubuntu/.hermes/config.yaml
gateway:
  port: 8000
  delivery: telegram

model:
  default: qwen-plus
  provider: alibaba

terminal:
  backend: local
  timeout: 300

mcp_servers:
  marketing:
    command: python3
    args: [-m, marketing]
    cwd: /home/ubuntu/hermes-marketing
    env:
      PYTHONPATH: /home/ubuntu/hermes-marketing
      BLUESKY_HANDLE: ${BLUESKY_HANDLE}
      BLUESKY_APP_PASSWORD: ${BLUESKY_APP_PASSWORD}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      LEMONSQUEEZY_API_KEY: ${LEMONSQUEEZY_API_KEY}
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      TELEGRAM_HOME_CHANNEL: ${TELEGRAM_HOME_CHANNEL}
```

### 4.5 systemd 서비스
```bash
sudo tee /etc/systemd/system/hermes-gateway.service <<'EOF'
[Unit]
Description=Hermes Business Agent Gateway
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/hermes-business/hermes-agent
EnvironmentFile=/home/ubuntu/.hermes/.env
Environment=HERMES_HOME=/home/ubuntu/.hermes
ExecStart=/usr/bin/python3 -m gateway.run
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable hermes-gateway --now
sudo systemctl status hermes-gateway
```

### 4.6 SOUL.md (identity)
프로젝트별 다름. 37_BA의 `deploy/SOUL.md`를 참고해서 본인 비즈니스에 맞게 수정. 핵심 섹션:
- Identity (역할, 목표 매출, 타겟)
- Honesty Rules (거짓 보고 = SHUTDOWN)
- Banned Actions (Reddit API, X 크레딧 자동 구매 등)
- Hard-coded values (체크아웃 URL, 예산 한도)

### 4.7 SKILL.md (실행 사이클)
`~/.hermes/skills/business/<프로젝트명>-cycle/SKILL.md` 작성. 표준 STEP:
1. verify-metrics + inventory 실행 → BLOG_N/VISITORS/REVENUE 추출
2. phase 결정 (BUILD/DISTRIBUTE/CONVERT/OPTIMIZE)
3. 해당 phase 실행
4. daily_log append
5. Telegram 리포트

37_BA의 `deploy/skills/business/notion-blog-cycle/SKILL.md` 통째로 복사 후 수정 권장.

### 4.8 크론 설정
```bash
# /home/ubuntu/.hermes/cron/jobs.json
cat > /home/ubuntu/.hermes/cron/jobs.json <<'EOF'
{
  "jobs": [
    {
      "id": "myproj-cycle-1",
      "name": "myproj-cycle",
      "schedule": {"kind": "interval", "minutes": 240, "display": "every 240m"},
      "skill": "myproj-cycle",
      "deliver": "telegram",
      "enabled": true,
      "state": "scheduled"
    }
  ]
}
EOF

sudo systemctl restart hermes-gateway
```

---

## 5. 첫 크론 실행 검증

### 5.1 수동 트리거 (즉시 실행)
```bash
# Hermes API로 sk직접 호출 (실제 명령은 hermes-agent 구조에 따라 다름)
curl -X POST http://localhost:8000/api/cron/trigger \
  -H "Content-Type: application/json" \
  -d '{"job_id": "myproj-cycle-1"}'

# 또는 systemd 로그 보면서 다음 자동 실행 대기
sudo journalctl -u hermes-gateway -f
```

### 5.2 결과 확인
```bash
# daily_log 첫 엔트리 확인
tail -3 /home/ubuntu/.hermes/memory/company/daily_log

# 사이트 외부 접근
curl -I http://$(curl -s ifconfig.me)/myproj/

# Telegram 리포트 도착 확인 (운영자 폰)
```

### 5.3 verify-metrics.sh 작성 (필수)
```bash
mkdir -p /home/ubuntu/<myproj>/deploy/harness
cat > /home/ubuntu/<myproj>/deploy/harness/verify-metrics.sh <<'EOF'
#!/bin/bash
source /home/ubuntu/.hermes/.env
echo "=== METRICS $(date +%Y-%m-%d) ==="

# Revenue (Lemon Squeezy 예시)
echo "[REVENUE]"
curl -s "https://api.lemonsqueezy.com/v1/stores/$LEMONSQUEEZY_STORE_ID" \
  -H "Authorization: Bearer $LEMONSQUEEZY_API_KEY" \
  -H "Accept: application/vnd.api+json" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); a=d['data']['attributes']; print('total_revenue:', a['total_revenue']); print('total_sales:', a['total_sales'])"

# Traffic (.gz 합산 — 37_BA에서 배운 교훈)
echo ""
echo "[TRAFFIC]"
LOGS=$(ls /var/log/nginx/access.log{,.1,.2.gz,.3.gz,.4.gz,.5.gz,.6.gz,.7.gz} 2>/dev/null)
if [ -n "$LOGS" ]; then
  TOTAL=$(sudo zcat -f $LOGS 2>/dev/null | wc -l)
  SELF=$(sudo zcat -f $LOGS 2>/dev/null | grep -cE "^(127\.0\.0\.1|$OCI_VM_IP)")
  echo "external_visitors: $((TOTAL - SELF))"
fi
EOF
chmod +x /home/ubuntu/<myproj>/deploy/harness/verify-metrics.sh
```

---

## 6. 트러블슈팅 (37_BA에서 배운 것)

| 증상 | 원인 | 해결 |
|------|------|------|
| 외부 `curl http://$IP/` 타임아웃 | 재부팅 후 iptables 80/443 사라짐 | `sudo iptables -I INPUT 5 -p tcp --dport 80 -j ACCEPT && sudo netfilter-persistent save` |
| `external_visitors=0` 갑자기 | nginx logrotate 후 .gz 못 읽음 | verify-metrics에 `zcat -f` 사용 |
| `Out of host capacity` (ARM A1) | 인기 리전 ARM 만석 | E4.Flex로 fallback 또는 새벽 재시도 |
| 에이전트 거짓 보고 | LLM이 검증 없이 SUCCESS 보고 | SOUL.md에 Honesty Rules + STEP에 verify 강제 |
| Telegram 이모지 깨짐 | curl UTF-8 인코딩 | `[OK]/[WARN]/[FAIL]` 텍스트 사용 |
| `cron` approval 차단 | Tirith Security Scanner | `.env`에 `TIRITH_ENABLED=false` |
| MCP 서브프로세스에 env 안 감 | `_build_safe_env()`가 필터 | `config.yaml`의 `mcp_servers.<name>.env`에 명시 |
| Reddit API 신청 거부 | 2025-11 Responsible Builder Policy | 네이버/X/Bluesky로 우회 |
| LS POST /v1/products 미지원 | LS API readonly 일부 | Playwright로 대시보드 자동화 |

---

## 7. Always Free Tier 한도 (Oracle)

| 리소스 | 무료 한도 |
|--------|----------|
| ARM VM | 4 OCPU / 24GB RAM (1대 또는 분할) |
| AMD VM | 2× E2.1.Micro 또는 1× E4.Flex (제한적) |
| Boot Volume | 200GB (2× 100GB) |
| Object Storage | 20GB |
| Egress | 10TB/월 |
| Load Balancer | 1대 (10Mbps) |

> Pay As You Go 업그레이드해도 Always Free 자원은 무과금 유지. 다만 추가 자원 쓰면 과금 시작.

---

## 8. 다음 단계 (선택)

- **PostHog 통합**: 사용자 행동 분석 (MCP 있음)
- **Resend 이메일**: 리드 캡처 + 뉴스레터
- **GitHub Actions**: 코드 푸시 시 자동 배포
- **Cloudflare**: DNS + DDoS 보호
- **모니터링**: Grafana + Prometheus (자체 호스팅) 또는 UptimeRobot 무료

---

## 부록 A. 참고 문서

- 현재 37_BA 운영 정보: `D:/Data/37_BA/docs/external-briefing/ORACLE_DEPLOYMENT.md`
- 37_BA env 실제 파일: `D:/Data/37_BA/deploy/.env` (gitignored)
- 메모리 인덱스: `D:/DevCache/claude-data/projects/D--Data-37-BA/memory/MEMORY.md`

---

*작성: 2026-04-26 / 검증: 37_BA Phase 1 인프라*
