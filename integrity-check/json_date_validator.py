"""
JSON Date Field Validator
==========================

JSON 파일의 날짜 필드를 검증하고 이상값을 찾아내는 도구입니다.

사용법 (Usage)
-------------

1. 기본 사용 (단일 필드 검증)
   $ python json_date_validator.py --path ./data/uploads --field program_broadcasted_at

2. 여러 폴더 검증
   $ python json_date_validator.py --path ./data/uploads \
       --folders upload_20251224_001 upload_20251225_001 \
       --field program_broadcasted_at

3. 여러 필드 동시 검증
   $ python json_date_validator.py --path ./data/uploads \
       --field program_broadcasted_at created_at updated_at

4. 날짜 형식 지정
   $ python json_date_validator.py --path ./data \
       --field date_field \
       --date-formats "%Y%m%d" "%Y-%m-%d"

5. 재귀 검색
   $ python json_date_validator.py --path ./data --field date --recursive

기능 (Features)
---------------
✓ 날짜 형식 검증 (YYYYMMDD, YYYY-MM-DD 등)
✓ 여러 필드 동시 검증
✓ 누락/이상값/오류 파일 분류
✓ 상세 리포트 자동 생성
✓ 재귀적 폴더 탐색 지원

날짜 형식 (Date Formats)
------------------------
기본 지원 형식:
  - YYYYMMDD (예: 20250115)
  - YYYY-MM-DD (예: 2025-01-15)

커스텀 형식 지정:
  --date-formats "%Y/%m/%d" "%d-%m-%Y"

출력 (Output)
-------------
validation_results/
├── invalid_dates_{timestamp}.txt    # 이상값 파일 목록
├── invalid_dates_{timestamp}.json   # JSON 형식 결과
└── summary_{timestamp}.txt          # 요약 통계

디렉토리 구조 (Directory Structure)
-----------------------------------
project/
├── data/
│   └── uploads/
│       ├── upload_20251224_001/
│       │   ├── file1.json
│       │   └── file2.json
│       └── upload_20251225_001/
├── validation_results/  # 자동 생성
└── json_date_validator.py

옵션 (Options)
--------------
  --path PATH              JSON 파일이 있는 기본 경로 (필수)
  --folders NAMES          검증할 특정 폴더명 (선택)
  --field FIELDS           검증할 날짜 필드명 (필수, 여러 개 가능)
  --date-formats FORMATS   날짜 형식 (기본: %Y%m%d, %Y-%m-%d)
  --year-range MIN MAX     유효한 연도 범위 (기본: 1900-2100)
  --output-dir DIR         결과 저장 디렉토리 (기본: validation_results)
  --recursive              하위 폴더까지 재귀 검색
  --quiet                  최소한의 출력만 표시
  -h, --help               도움말 출력

예제 (Examples)
---------------

# 1. 방송일자 필드 검증
$ python json_date_validator.py \
    --path ./uploads \
    --field program_broadcasted_at

# 2. 여러 날짜 필드 검증
$ python json_date_validator.py \
    --path ./data \
    --field created_at updated_at published_at

# 3. 특정 폴더만 검증
$ python json_date_validator.py \
    --path ./uploads \
    --folders upload_20251224_001 upload_20251225_001 \
    --field program_broadcasted_at

# 4. 연도 범위 제한
$ python json_date_validator.py \
    --path ./data \
    --field date \
    --year-range 2020 2025
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


class JSONDateValidator:
    """JSON 파일의 날짜 필드를 검증하는 클래스"""
    
    def __init__(
        self,
        base_path: str,
        output_dir: str = "validation_results",
        date_formats: Optional[List[str]] = None,
        year_range: Tuple[int, int] = (1900, 2100),
        quiet: bool = False
    ):
        """
        Args:
            base_path: JSON 파일이 있는 기본 경로
            output_dir: 결과 저장 디렉토리
            date_formats: 검증할 날짜 형식 리스트
            year_range: 유효한 연도 범위 (min, max)
            quiet: True면 최소한의 출력만
        """
        self.base_path = Path(base_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # 기본 날짜 형식
        self.date_formats = date_formats or ["%Y%m%d", "%Y-%m-%d"]
        self.year_range = year_range
        self.quiet = quiet
        
        if not self.base_path.exists():
            raise ValueError(f"경로가 존재하지 않습니다: {self.base_path}")
    
    def log(self, message: str, force: bool = False):
        """로그 출력 (quiet 모드 고려)"""
        if not self.quiet or force:
            print(message)
    
    def get_json_files(
        self,
        folder_path: Path,
        recursive: bool = False
    ) -> List[Path]:
        """
        폴더에서 JSON 파일 목록을 가져옵니다
        
        Args:
            folder_path: 탐색할 폴더 경로
            recursive: True면 하위 폴더까지 재귀 탐색
            
        Returns:
            JSON 파일 경로 리스트
        """
        if recursive:
            return list(folder_path.rglob("*.json"))
        else:
            return list(folder_path.glob("*.json"))
    
    def is_valid_date_format(self, date_str: str) -> Tuple[bool, Optional[str]]:
        """
        날짜 문자열이 유효한 형식인지 확인
        
        Args:
            date_str: 검증할 날짜 문자열
            
        Returns:
            (유효 여부, 매칭된 형식)
        """
        if not date_str or not isinstance(date_str, str):
            return False, None
        
        for date_format in self.date_formats:
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                year = parsed_date.year
                
                # 연도 범위 확인
                if self.year_range[0] <= year <= self.year_range[1]:
                    return True, date_format
            except (ValueError, TypeError):
                continue
        
        return False, None
    
    def check_json_file(
        self,
        json_path: Path,
        target_fields: List[str]
    ) -> Dict[str, Dict]:
        """
        JSON 파일을 읽고 날짜 필드를 검증합니다
        
        Args:
            json_path: JSON 파일 경로
            target_fields: 검증할 필드명 리스트
            
        Returns:
            필드별 검증 결과 딕셔너리
        """
        results = {}
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for field in target_fields:
                date_value = data.get(field, None)
                
                if date_value is None:
                    results[field] = {
                        'status': 'missing',
                        'file_id': json_path.stem,
                        'file_path': str(json_path),
                        'value': None,
                        'reason': f'{field} 필드 없음'
                    }
                else:
                    is_valid, matched_format = self.is_valid_date_format(date_value)
                    
                    if not is_valid:
                        results[field] = {
                            'status': 'invalid',
                            'file_id': json_path.stem,
                            'file_path': str(json_path),
                            'value': date_value,
                            'reason': f'잘못된 형식: {date_value}'
                        }
                    else:
                        results[field] = {
                            'status': 'valid',
                            'file_id': json_path.stem,
                            'file_path': str(json_path),
                            'value': date_value,
                            'format': matched_format,
                            'reason': 'OK'
                        }
        
        except json.JSONDecodeError as e:
            for field in target_fields:
                results[field] = {
                    'status': 'error',
                    'file_id': json_path.stem,
                    'file_path': str(json_path),
                    'value': None,
                    'reason': f'JSON 파싱 오류: {str(e)}'
                }
        
        except Exception as e:
            for field in target_fields:
                results[field] = {
                    'status': 'error',
                    'file_id': json_path.stem,
                    'file_path': str(json_path),
                    'value': None,
                    'reason': f'읽기 오류: {str(e)}'
                }
        
        return results
    
    def validate_folders(
        self,
        folder_names: Optional[List[str]] = None,
        target_fields: List[str] = None,
        recursive: bool = False
    ) -> Dict:
        """
        폴더들의 JSON 파일을 검증합니다
        
        Args:
            folder_names: 검증할 폴더명 리스트 (None이면 base_path 전체)
            target_fields: 검증할 필드명 리스트
            recursive: 재귀 탐색 여부
            
        Returns:
            전체 검증 결과
        """
        if not target_fields:
            raise ValueError("검증할 필드명을 지정해야 합니다 (--field)")
        
        self.log("="*70, force=True)
        self.log("🔍 JSON 날짜 필드 검증 시작", force=True)
        self.log("="*70, force=True)
        self.log(f"📂 기본 경로: {self.base_path}", force=True)
        self.log(f"📋 검증 필드: {', '.join(target_fields)}", force=True)
        self.log(f"📅 날짜 형식: {', '.join(self.date_formats)}", force=True)
        self.log("")
        
        # 폴더 목록 결정
        if folder_names:
            folders = [self.base_path / folder for folder in folder_names]
            # 존재하지 않는 폴더 필터링
            folders = [f for f in folders if f.exists() and f.is_dir()]
            if not folders:
                self.log("❌ 지정한 폴더를 찾을 수 없습니다.", force=True)
                return {}
        else:
            # base_path 자체를 검증
            folders = [self.base_path]
        
        # 필드별 결과 저장
        all_results = {field: defaultdict(list) for field in target_fields}
        
        for folder in folders:
            folder_name = folder.name
            self.log(f"📁 [{folder_name}] 검사 중...")
            
            json_files = self.get_json_files(folder, recursive)
            self.log(f"   총 JSON 파일: {len(json_files)}개")
            
            if not json_files:
                self.log(f"   ⚠️ JSON 파일이 없습니다.\n")
                continue
            
            # 필드별 카운터
            field_counters = {
                field: {'valid': 0, 'invalid': 0, 'missing': 0, 'error': 0}
                for field in target_fields
            }
            
            for idx, json_file in enumerate(json_files, 1):
                if idx % 1000 == 0 or idx == 1:
                    self.log(f"   [{idx}/{len(json_files)}] 처리 중...")
                
                results = self.check_json_file(json_file, target_fields)
                
                for field, result in results.items():
                    status = result['status']
                    all_results[field][status].append(result)
                    field_counters[field][status] += 1
            
            # 폴더별 통계 출력
            self.log(f"\n   ✅ 검사 완료")
            for field in target_fields:
                counter = field_counters[field]
                self.log(f"   [{field}]")
                self.log(f"      유효: {counter['valid']}개")
                self.log(f"      이상값: {counter['invalid']}개")
                self.log(f"      누락: {counter['missing']}개")
                self.log(f"      오류: {counter['error']}개")
            self.log("")
        
        return all_results
    
    def save_results(
        self,
        results: Dict,
        target_fields: List[str]
    ):
        """
        검증 결과를 파일로 저장합니다
        
        Args:
            results: 검증 결과 딕셔너리
            target_fields: 검증한 필드명 리스트
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 텍스트 리포트
        report_file = self.output_dir / f"invalid_dates_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("JSON 날짜 필드 검증 리포트\n")
            f.write("="*70 + "\n")
            f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"검증 필드: {', '.join(target_fields)}\n")
            f.write("="*70 + "\n\n")
            
            for field in target_fields:
                field_results = results[field]
                
                f.write(f"\n{'='*70}\n")
                f.write(f"필드: {field}\n")
                f.write(f"{'='*70}\n\n")
                
                # 이상값
                if field_results['invalid']:
                    f.write(f"❌ 잘못된 형식 ({len(field_results['invalid'])}개):\n")
                    f.write("-"*70 + "\n")
                    for result in sorted(field_results['invalid'], key=lambda x: x['file_id']):
                        f.write(f"{result['file_id']}: {result['value']}\n")
                    f.write("\n")
                
                # 누락
                if field_results['missing']:
                    f.write(f"⚠️ 필드 누락 ({len(field_results['missing'])}개):\n")
                    f.write("-"*70 + "\n")
                    for result in sorted(field_results['missing'], key=lambda x: x['file_id']):
                        f.write(f"{result['file_id']}\n")
                    f.write("\n")
                
                # 오류
                if field_results['error']:
                    f.write(f"❌ 읽기 오류 ({len(field_results['error'])}개):\n")
                    f.write("-"*70 + "\n")
                    for result in sorted(field_results['error'], key=lambda x: x['file_id']):
                        f.write(f"{result['file_id']}: {result['reason']}\n")
                    f.write("\n")
                
                # 통계
                f.write("-"*70 + "\n")
                f.write(f"유효: {len(field_results['valid'])}개\n")
                f.write(f"이상값: {len(field_results['invalid'])}개\n")
                f.write(f"누락: {len(field_results['missing'])}개\n")
                f.write(f"오류: {len(field_results['error'])}개\n")
        
        # JSON 리포트
        json_file = self.output_dir / f"invalid_dates_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # 요약 통계
        summary_file = self.output_dir / f"summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("검증 요약\n")
            f.write("="*70 + "\n\n")
            
            for field in target_fields:
                field_results = results[field]
                total = sum(len(field_results[status]) for status in ['valid', 'invalid', 'missing', 'error'])
                
                f.write(f"[{field}]\n")
                f.write(f"  전체: {total}개\n")
                f.write(f"  유효: {len(field_results['valid'])}개 ({len(field_results['valid'])/total*100:.1f}%)\n")
                f.write(f"  이상값: {len(field_results['invalid'])}개\n")
                f.write(f"  누락: {len(field_results['missing'])}개\n")
                f.write(f"  오류: {len(field_results['error'])}개\n\n")
        
        self.log("\n📄 결과 저장:", force=True)
        self.log(f"   리포트: {report_file}", force=True)
        self.log(f"   JSON: {json_file}", force=True)
        self.log(f"   요약: {summary_file}", force=True)
    
    def print_summary(self, results: Dict, target_fields: List[str]):
        """검증 결과 요약을 출력합니다"""
        self.log("\n" + "="*70, force=True)
        self.log("✅ 검증 완료", force=True)
        self.log("="*70, force=True)
        
        for field in target_fields:
            field_results = results[field]
            total = sum(len(field_results[status]) for status in ['valid', 'invalid', 'missing', 'error'])
            
            self.log(f"\n📊 [{field}] 통계:", force=True)
            self.log(f"   전체: {total}개", force=True)
            self.log(f"   유효: {len(field_results['valid'])}개", force=True)
            self.log(f"   이상값: {len(field_results['invalid'])}개", force=True)
            self.log(f"   누락: {len(field_results['missing'])}개", force=True)
            self.log(f"   오류: {len(field_results['error'])}개", force=True)
            
            # 이상값 샘플 출력
            if field_results['invalid']:
                self.log(f"\n   ⚠️ 이상값 샘플:", force=True)
                for result in field_results['invalid'][:5]:
                    self.log(f"      {result['file_id']}: {result['value']}", force=True)
                if len(field_results['invalid']) > 5:
                    self.log(f"      ... 외 {len(field_results['invalid']) - 5}개", force=True)


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="JSON 날짜 필드 검증 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--path',
        required=True,
        help='JSON 파일이 있는 기본 경로'
    )
    parser.add_argument(
        '--folders',
        nargs='+',
        help='검증할 특정 폴더명 (생략 시 전체 검증)'
    )
    parser.add_argument(
        '--field',
        nargs='+',
        required=True,
        help='검증할 날짜 필드명 (여러 개 가능)'
    )
    parser.add_argument(
        '--date-formats',
        nargs='+',
        help='날짜 형식 (예: %%Y%%m%%d %%Y-%%m-%%d)'
    )
    parser.add_argument(
        '--year-range',
        nargs=2,
        type=int,
        default=[1900, 2100],
        metavar=('MIN', 'MAX'),
        help='유효한 연도 범위 (기본: 1900 2100)'
    )
    parser.add_argument(
        '--output-dir',
        default='validation_results',
        help='결과 저장 디렉토리 (기본: validation_results)'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='하위 폴더까지 재귀 탐색'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='최소한의 출력만 표시'
    )
    
    args = parser.parse_args()
    
    try:
        # 검증기 생성
        validator = JSONDateValidator(
            base_path=args.path,
            output_dir=args.output_dir,
            date_formats=args.date_formats,
            year_range=tuple(args.year_range),
            quiet=args.quiet
        )
        
        # 검증 실행
        results = validator.validate_folders(
            folder_names=args.folders,
            target_fields=args.field,
            recursive=args.recursive
        )
        
        if results:
            # 결과 저장
            validator.save_results(results, args.field)
            
            # 요약 출력
            validator.print_summary(results, args.field)
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
