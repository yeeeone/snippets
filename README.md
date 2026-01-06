# Data Processing Utilities

데이터 처리 및 검증을 위한 Python 유틸리티 모음입니다. 클라우드 스토리지 관리, 데이터 분석, 무결성 검증 등의 작업을 자동화합니다.

## 📁 프로젝트 구조

```
.
├── cloud-utilization/
│   └── s3_file_transfer.py         # S3 파일 업로드/다운로드
├── export-report/
│   └── video_stats_analyzer.py     # 비디오 통계 분석
└── integrity-check/
    ├── file_pair_checker.py        # 파일 쌍 검증
    ├── json_date_validator.py      # 날짜 필드 검증
    └── json_field_fixer.py         # 필드 값 일괄 수정
```

## 🛠️ 주요 도구

### 1. S3 File Transfer (`cloud-utilization/`)

S3 호환 스토리지와 로컬 파일 시스템 간 파일 전송 도구

**주요 기능:**
- 📤 폴더 업로드 (전체/선택적)
- 📥 폴더 다운로드
- 📋 S3 객체 목록 조회
- 🔍 Dry-run 모드
- 🌐 AWS S3, NCP Object Storage 등 지원

**사용 예시:**
```bash
# 업로드
python s3_file_transfer.py upload --local-path ./data --s3-path project/data

# 다운로드
python s3_file_transfer.py download --s3-path project/data --local-path ./downloads

# 목록 조회
python s3_file_transfer.py list --s3-path project/data --recursive
```

**필수 환경 변수:**
```bash
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET_NAME=your-bucket-name
S3_ENDPOINT_URL=https://s3.amazonaws.com  # 선택사항
S3_REGION=us-east-1
```

---

### 2. Video Stats Analyzer (`export-report/`)

JSON 매니페스트에서 비디오 길이 통계를 분석하고 리포트 생성

**주요 기능:**
- 📊 비디오 길이 통계 (평균, 최소, 최대, 중간값)
- 📈 길이별 분포 분석
- 📅 날짜 범위 필터링
- 📁 증분 처리 (새 폴더만 분석)
- 📄 CSV 리포트 생성

**사용 예시:**
```bash
# 전체 폴더 분석
python video_stats_analyzer.py --base-path ./data/uploads

# 날짜 범위 지정
python video_stats_analyzer.py --start-date 20250901 --end-date 20250930

# 폴더 목록만 확인
python video_stats_analyzer.py --list --start-date 20250901

# 재처리
python video_stats_analyzer.py --reprocess
```

**입력 형식:**
```
data/uploads/
├── upload_20250901_001/
│   └── manifests/
│       ├── video1.json  # {"duration": "00:05:30", ...}
│       └── video2.json
```

**출력:**
```
stats_output/
├── video_stats_upload_20250901_001.csv
├── video_durations_raw_upload_20250901_001.csv
└── invalid_files_upload_20250901_001.csv
```

---

### 3. File Pair Checker (`integrity-check/`)

비디오 파일과 JSON 매니페스트의 쌍 일치 여부 검증

**주요 기능:**
- 🔍 파일 쌍 검증 (MP4 ↔ JSON)
- 📊 누락 파일 리포트
- 📁 여러 폴더 일괄 검증
- 📈 통계 생성

**사용 예시:**
```bash
# 단일 폴더 검증
python file_pair_checker.py --path ./data/upload_001

# 여러 폴더 검증
python file_pair_checker.py --path ./data \
    --folders upload_001 upload_002 upload_003

# 비디오 확장자 지정
python file_pair_checker.py --path ./data --video-ext .mov
```

**출력:**
```
pair_check_results/
├── pair_check_20250106_143022.txt   # 상세 리포트
├── pair_check_20250106_143022.json  # JSON 결과
└── summary_20250106_143022.txt      # 요약 통계
```

---

### 4. JSON Date Validator (`integrity-check/`)

JSON 파일의 날짜 필드를 검증하고 이상값 탐지

**주요 기능:**
- 📅 날짜 형식 검증 (YYYYMMDD, YYYY-MM-DD 등)
- 🔍 여러 필드 동시 검증
- ⚠️ 이상값/누락/오류 분류
- 📊 상세 리포트 생성

**사용 예시:**
```bash
# 단일 필드 검증
python json_date_validator.py --path ./data --field program_broadcasted_at

# 여러 필드 검증
python json_date_validator.py --path ./data \
    --field created_at updated_at published_at

# 날짜 형식 지정
python json_date_validator.py --path ./data \
    --field date \
    --date-formats "%Y/%m/%d" "%d-%m-%Y"

# 연도 범위 제한
python json_date_validator.py --path ./data \
    --field date \
    --year-range 2020 2025
```

**출력:**
```
validation_results/
├── invalid_dates_20250106_143022.txt   # 이상값 리포트
├── invalid_dates_20250106_143022.json  # JSON 결과
└── summary_20250106_143022.txt         # 요약 통계
```

---

### 5. JSON Field Fixer (`integrity-check/`)

JSON 필드의 잘못된 값을 찾아서 일괄 수정

**주요 기능:**
- ✏️ 특정 값 자동 검색 및 수정
- 🛡️ 자동 백업 생성
- 🔍 Dry-run 모드 (미리보기)
- 📊 상세 수정 로그

**사용 예시:**
```bash
# 미리보기 (Dry-run)
python json_field_fixer.py \
    --path ./data \
    --field program_broadcasted_at \
    --find 20169715 \
    --replace 20160715 \
    --dry-run

# 실제 수정
python json_field_fixer.py \
    --path ./data \
    --field program_broadcasted_at \
    --find 20169715 \
    --replace 20160715

# 여러 값 동시 수정
python json_field_fixer.py \
    --path ./data \
    --field date \
    --find 20169715 130416-18 20251300 \
    --replace 20160715

# 백업 없이 수정 (주의!)
python json_field_fixer.py \
    --path ./data \
    --field date \
    --find 20169715 \
    --replace 20160715 \
    --no-backup
```

**출력:**
```
fix_results/
├── fix_log_20250106_143022.txt      # 상세 수정 로그
├── fix_log_20250106_143022.json     # JSON 로그
└── fix_summary_20250106_143022.txt  # 요약 통계

# 백업 파일 (기본 생성)
data/
└── file1_backup_20250106_143022.json
```

---

## 🚀 시작하기

### 필수 요구사항

```bash
Python 3.7+
```

### 의존성 설치

```bash
# 공통 패키지
pip install pandas

# S3 전송용 (선택사항)
pip install boto3 python-dotenv
```

### 환경 설정

1. **S3 전송용** (`.env` 파일 생성):
```bash
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET_NAME=your-bucket-name
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_REGION=us-east-1
```

2. **기타 도구들**: 환경 설정 불필요 (로컬 파일만 사용)

---

## 📖 사용 시나리오

### 시나리오 1: 데이터 업로드 및 검증

```bash
# 1. 데이터를 S3에 업로드
python s3_file_transfer.py upload \
    --local-path ./raw_data \
    --s3-path project/uploads/20250106

# 2. 파일 쌍 검증 (비디오 ↔ JSON)
python file_pair_checker.py \
    --path ./raw_data

# 3. 날짜 필드 검증
python json_date_validator.py \
    --path ./raw_data \
    --field program_broadcasted_at
```

### 시나리오 2: 데이터 정제 및 분석

```bash
# 1. 잘못된 날짜 수정
python json_field_fixer.py \
    --path ./data \
    --field program_broadcasted_at \
    --find 20169715 \
    --replace 20160715

# 2. 비디오 통계 분석
python video_stats_analyzer.py \
    --base-path ./data \
    --start-date 20250101 \
    --end-date 20250131
```

### 시나리오 3: 정기 모니터링

```bash
# 1. 새 데이터 폴더 확인
python video_stats_analyzer.py --list

# 2. 새 폴더만 분석 (증분 처리)
python video_stats_analyzer.py

# 3. S3에서 최신 데이터 다운로드
python s3_file_transfer.py download \
    --s3-path project/latest \
    --local-path ./downloads
```

---

## 📊 출력 형식

모든 도구는 다음 형식으로 결과를 출력합니다:

### 텍스트 리포트 (`.txt`)
- 사람이 읽기 쉬운 형식
- 상세한 통계 및 오류 내역
- 샘플 데이터 포함

### JSON 리포트 (`.json`)
- 프로그래밍 가능한 형식
- 전체 결과 데이터
- 추가 분석용

### CSV 리포트 (`.csv`)
- 표 형식 데이터
- Excel 호환
- 데이터 분석 및 시각화용

---

## ⚙️ 공통 옵션

대부분의 도구는 다음 옵션을 지원합니다:

```bash
--path PATH              # 작업 대상 경로
--folders NAMES          # 특정 폴더만 처리
--output-dir DIR         # 결과 저장 디렉토리
--recursive              # 하위 폴더 재귀 탐색
--dry-run                # 미리보기 모드
--quiet                  # 최소한의 출력만
-h, --help               # 도움말
```

---

## 🔒 안전 기능

### 자동 백업
- `json_field_fixer.py`는 기본적으로 수정 전 백업 생성
- 백업 파일: `{원본파일}_backup_{timestamp}.json`

### Dry-run 모드
- 실제 작업 없이 미리보기
- 안전한 테스트 가능
- 모든 수정 도구에서 지원

### 에러 처리
- 개별 파일 오류가 전체 작업을 중단하지 않음
- 상세한 오류 로그 생성
- 처리 가능한 파일은 계속 진행

---

## 📝 로그 및 디버깅

각 도구는 다음 정보를 로그에 기록합니다:

- ✅ 성공한 작업
- ⚠️ 경고 (건너뛴 파일 등)
- ❌ 오류 (실패 원인 포함)
- 📊 통계 (처리된 파일 수, 소요 시간 등)

**로그 위치:**
```
{output_dir}/
├── {tool_name}_log_{timestamp}.txt
├── {tool_name}_log_{timestamp}.json
└── summary_{timestamp}.txt
```

---

## 🤝 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!

---

## 👤 작성자

[Your Name]

---

## 📚 추가 자료

각 스크립트 파일의 상단에 상세한 사용법이 포함되어 있습니다:

```bash
python {script_name}.py --help
```

또는 스크립트 파일을 직접 열어서 docstring을 확인하세요.
