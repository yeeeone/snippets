"""
JSON Field Value Fixer
=======================

JSON 파일에서 특정 필드의 잘못된 값을 찾아서 올바른 값으로 일괄 수정하는 도구입니다.

사용법 (Usage)
-------------

1. 기본 사용 (특정 값 수정)
   $ python json_field_fixer.py \
       --path ./data/uploads/upload_20251219_001 \
       --field program_broadcasted_at \
       --find 20169715 \
       --replace 20160715

2. 여러 값 동시 수정
   $ python json_field_fixer.py \
       --path ./data \
       --field date \
       --find 20169715 130416-18 20251300 \
       --replace 20160715

3. 여러 폴더 일괄 수정
   $ python json_field_fixer.py \
       --path ./uploads \
       --folders upload_20251219_001 upload_20251220_001 \
       --field program_broadcasted_at \
       --find 20169715 \
       --replace 20160715

4. 미리보기 모드 (실제 수정 안함)
   $ python json_field_fixer.py \
       --path ./data \
       --field date \
       --find 20169715 \
       --replace 20160715 \
       --dry-run

5. 백업 없이 수정 (주의!)
   $ python json_field_fixer.py \
       --path ./data \
       --field date \
       --find 20169715 \
       --replace 20160715 \
       --no-backup

기능 (Features)
---------------
✓ 특정 값을 가진 파일 자동 검색
✓ 여러 값을 동일한 값으로 일괄 수정
✓ 수정 전 자동 백업 생성
✓ Dry-run 모드로 미리보기
✓ 상세한 수정 로그 생성
✓ 재귀적 폴더 탐색 지원

백업 (Backup)
-------------
기본적으로 수정 전 원본 파일을 백업합니다:
- 백업 위치: {파일명}_backup_{timestamp}.json
- 백업 비활성화: --no-backup 옵션 사용

출력 (Output)
-------------
fix_results/
├── fix_log_{timestamp}.txt          # 수정 로그
├── fix_log_{timestamp}.json         # JSON 형식 로그
└── fix_summary_{timestamp}.txt      # 요약 통계

디렉토리 구조 (Directory Structure)
-----------------------------------
project/
├── data/
│   └── uploads/
│       ├── upload_20251219_001/
│       │   ├── file1.json
│       │   ├── file1_backup_20250106.json  # 백업
│       │   └── file2.json
│       └── upload_20251220_001/
├── fix_results/  # 자동 생성
└── json_field_fixer.py

옵션 (Options)
--------------
  --path PATH              JSON 파일이 있는 기본 경로 (필수)
  --folders NAMES          수정할 특정 폴더명 (선택)
  --field FIELD            수정할 필드명 (필수)
  --find VALUES            찾을 값들 (여러 개 가능)
  --replace VALUE          변경할 값 (필수)
  --output-dir DIR         결과 저장 디렉토리 (기본: fix_results)
  --recursive              하위 폴더까지 재귀 검색
  --dry-run                실제 수정 없이 미리보기만
  --no-backup              백업 파일 생성 안함
  --quiet                  최소한의 출력만 표시
  -h, --help               도움말 출력

예제 (Examples)
---------------

# 1. 날짜 오타 수정 (20169715 → 20160715)
$ python json_field_fixer.py \
    --path ./uploads/upload_20251219_001 \
    --field program_broadcasted_at \
    --find 20169715 \
    --replace 20160715

# 2. 여러 오타를 한 번에 수정
$ python json_field_fixer.py \
    --path ./data \
    --field date \
    --find 20169715 130416-18 20251300 \
    --replace 20160715

# 3. 미리보기 후 수정
$ python json_field_fixer.py --path ./data --field date \
    --find 20169715 --replace 20160715 --dry-run

# 실제 수정
$ python json_field_fixer.py --path ./data --field date \
    --find 20169715 --replace 20160715

# 4. 여러 폴더 일괄 수정
$ python json_field_fixer.py \
    --path ./uploads \
    --folders folder1 folder2 folder3 \
    --field program_broadcasted_at \
    --find 20169715 \
    --replace 20160715

주의사항 (Cautions)
-------------------
⚠️ --no-backup 옵션 사용 시 원본 파일이 영구적으로 수정됩니다
⚠️ 수정 전에는 반드시 --dry-run으로 확인하세요
✓ 기본적으로 백업이 자동 생성되므로 안전합니다

"""

import os
import json
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict


class JSONFieldFixer:
    """JSON 파일의 특정 필드 값을 수정하는 클래스"""
    
    def __init__(
        self,
        base_path: str,
        output_dir: str = "fix_results",
        backup: bool = True,
        dry_run: bool = False,
        quiet: bool = False
    ):
        """
        Args:
            base_path: JSON 파일이 있는 기본 경로
            output_dir: 결과 저장 디렉토리
            backup: 백업 생성 여부
            dry_run: True면 실제 수정 없이 미리보기만
            quiet: True면 최소한의 출력만
        """
        self.base_path = Path(base_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.backup = backup
        self.dry_run = dry_run
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
    
    def scan_for_target_values(
        self,
        folder_path: Path,
        field_name: str,
        target_values: List[str],
        recursive: bool = False
    ) -> Dict[Path, str]:
        """
        특정 필드에서 대상 값을 가진 파일들을 찾습니다
        
        Args:
            folder_path: 스캔할 폴더 경로
            field_name: 검색할 필드명
            target_values: 찾을 값들의 리스트
            recursive: 재귀 탐색 여부
            
        Returns:
            {파일 경로: 현재 값} 딕셔너리
        """
        file_data = {}
        json_files = self.get_json_files(folder_path, recursive)
        
        self.log(f"📖 폴더 스캔 중: {folder_path}")
        self.log(f"   JSON 파일: {len(json_files)}개\n")
        
        scanned_count = 0
        
        for json_file in json_files:
            scanned_count += 1
            
            if scanned_count % 100 == 0:
                self.log(f"   [{scanned_count}/{len(json_files)}] 스캔 중...")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                value = data.get(field_name, '')
                
                # 대상 값인지 확인
                if str(value) in target_values:
                    file_data[json_file] = value
                    self.log(f"   ✅ 발견: {json_file.name} = {value}")
            
            except Exception as e:
                self.log(f"   ⚠️ 읽기 오류 ({json_file.name}): {e}")
                continue
        
        self.log(f"\n   ✅ 스캔 완료: {scanned_count}개 검사, {len(file_data)}개 발견\n")
        return file_data
    
    def backup_file(self, file_path: Path) -> Optional[Path]:
        """
        파일 백업 생성
        
        Args:
            file_path: 백업할 파일 경로
            
        Returns:
            백업 파일 경로 또는 None
        """
        if not self.backup:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_name(
            f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        )
        
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            self.log(f"   ⚠️ 백업 실패 ({file_path.name}): {e}")
            return None
    
    def fix_file(
        self,
        file_path: Path,
        field_name: str,
        target_values: List[str],
        new_value: str
    ) -> Dict:
        """
        단일 파일의 필드 값을 수정합니다
        
        Args:
            file_path: 수정할 파일 경로
            field_name: 수정할 필드명
            target_values: 대상 값들
            new_value: 변경할 값
            
        Returns:
            수정 결과 딕셔너리
        """
        result = {
            'file': str(file_path),
            'file_name': file_path.name,
            'status': 'failed',
            'original_value': None,
            'new_value': new_value,
            'backup_path': None,
            'error': None
        }
        
        try:
            # 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_value = data.get(field_name, '')
            result['original_value'] = original_value
            
            # 대상 값이 아니면 건너뛰기
            if str(original_value) not in target_values:
                result['status'] = 'skipped'
                result['error'] = 'Not a target value'
                return result
            
            # Dry-run 모드
            if self.dry_run:
                result['status'] = 'dry_run'
                return result
            
            # 백업 생성
            if self.backup:
                backup_path = self.backup_file(file_path)
                if backup_path:
                    result['backup_path'] = str(backup_path)
            
            # 값 수정
            data[field_name] = new_value
            
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            result['status'] = 'success'
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def fix_folders(
        self,
        folder_names: Optional[List[str]],
        field_name: str,
        target_values: List[str],
        new_value: str,
        recursive: bool = False
    ) -> Dict:
        """
        폴더들의 JSON 파일을 수정합니다
        
        Args:
            folder_names: 수정할 폴더명 리스트 (None이면 base_path 전체)
            field_name: 수정할 필드명
            target_values: 찾을 값들
            new_value: 변경할 값
            recursive: 재귀 탐색 여부
            
        Returns:
            전체 수정 결과
        """
        self.log("="*70, force=True)
        self.log(f"🔧 {'[DRY-RUN] ' if self.dry_run else ''}JSON 필드 값 수정", force=True)
        self.log("="*70, force=True)
        self.log(f"📂 기본 경로: {self.base_path}", force=True)
        self.log(f"📋 필드: {field_name}", force=True)
        self.log(f"🔍 찾을 값: {', '.join(target_values)}", force=True)
        self.log(f"✏️  변경 값: {new_value}", force=True)
        self.log("")
        
        # 폴더 목록 결정
        if folder_names:
            folders = [self.base_path / folder for folder in folder_names]
            folders = [f for f in folders if f.exists() and f.is_dir()]
            if not folders:
                self.log("❌ 지정한 폴더를 찾을 수 없습니다.", force=True)
                return {}
        else:
            folders = [self.base_path]
        
        all_results = []
        
        for folder in folders:
            self.log(f"1️⃣ [{folder.name}] 대상 파일 검색\n", force=True)
            
            # 대상 파일 찾기
            target_files = self.scan_for_target_values(
                folder, field_name, target_values, recursive
            )
            
            if not target_files:
                self.log(f"   ⚠️ 수정할 파일이 없습니다.\n")
                continue
            
            self.log(f"   📝 수정 대상: {len(target_files)}개 파일\n", force=True)
            
            # 파일 수정
            self.log(f"2️⃣ 파일 수정 중\n", force=True)
            
            success_count = 0
            failed_count = 0
            
            for idx, (file_path, original_value) in enumerate(target_files.items(), 1):
                if idx % 50 == 0 or idx == 1:
                    self.log(f"   [{idx}/{len(target_files)}] 처리 중...")
                
                result = self.fix_file(file_path, field_name, target_values, new_value)
                all_results.append(result)
                
                if result['status'] == 'success' or result['status'] == 'dry_run':
                    success_count += 1
                else:
                    failed_count += 1
                    if result['error']:
                        self.log(f"      ⚠️ 실패 ({file_path.name}): {result['error']}")
            
            self.log(f"\n   ✅ 처리 완료", force=True)
            self.log(f"      {'미리보기' if self.dry_run else '수정'}: {success_count}개", force=True)
            self.log(f"      실패: {failed_count}개\n", force=True)
        
        return {
            'results': all_results,
            'field_name': field_name,
            'target_values': target_values,
            'new_value': new_value
        }
    
    def save_results(self, fix_data: Dict):
        """
        수정 결과를 저장합니다
        
        Args:
            fix_data: 수정 결과 딕셔너리
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = fix_data['results']
        
        # 텍스트 로그
        log_file = self.output_dir / f"fix_log_{timestamp}.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("JSON 필드 수정 로그\n")
            f.write("="*70 + "\n")
            f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"필드: {fix_data['field_name']}\n")
            f.write(f"찾은 값: {', '.join(fix_data['target_values'])}\n")
            f.write(f"변경 값: {fix_data['new_value']}\n")
            f.write(f"Dry-run: {'예' if self.dry_run else '아니오'}\n")
            f.write("="*70 + "\n\n")
            
            # 성공
            success_results = [r for r in results if r['status'] in ['success', 'dry_run']]
            if success_results:
                f.write(f"✅ {'미리보기' if self.dry_run else '수정 완료'} ({len(success_results)}개):\n")
                f.write("-"*70 + "\n")
                for result in success_results:
                    f.write(f"파일: {result['file_name']}\n")
                    f.write(f"  변경 전: {result['original_value']}\n")
                    f.write(f"  변경 후: {result['new_value']}\n")
                    if result['backup_path']:
                        f.write(f"  백업: {result['backup_path']}\n")
                    f.write("\n")
            
            # 실패
            failed_results = [r for r in results if r['status'] == 'failed']
            if failed_results:
                f.write(f"\n❌ 실패 ({len(failed_results)}개):\n")
                f.write("-"*70 + "\n")
                for result in failed_results:
                    f.write(f"파일: {result['file_name']}\n")
                    f.write(f"  오류: {result['error']}\n\n")
            
            # 통계
            f.write("="*70 + "\n")
            f.write("통계\n")
            f.write("="*70 + "\n")
            f.write(f"전체: {len(results)}개\n")
            f.write(f"{'미리보기' if self.dry_run else '수정'}: {len(success_results)}개\n")
            f.write(f"실패: {len(failed_results)}개\n")
        
        # JSON 로그
        json_file = self.output_dir / f"fix_log_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(fix_data, f, indent=2, ensure_ascii=False)
        
        # 요약
        summary_file = self.output_dir / f"fix_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("수정 요약\n")
            f.write("="*70 + "\n\n")
            f.write(f"필드: {fix_data['field_name']}\n")
            f.write(f"대상 값: {', '.join(fix_data['target_values'])}\n")
            f.write(f"변경 값: {fix_data['new_value']}\n\n")
            f.write(f"전체: {len(results)}개\n")
            f.write(f"{'미리보기' if self.dry_run else '수정'}: {len(success_results)}개\n")
            f.write(f"실패: {len(failed_results)}개\n")
        
        self.log("\n📄 결과 저장:", force=True)
        self.log(f"   로그: {log_file}", force=True)
        self.log(f"   JSON: {json_file}", force=True)
        self.log(f"   요약: {summary_file}", force=True)
    
    def print_summary(self, fix_data: Dict):
        """수정 결과 요약을 출력합니다"""
        results = fix_data['results']
        
        success_count = len([r for r in results if r['status'] in ['success', 'dry_run']])
        failed_count = len([r for r in results if r['status'] == 'failed'])
        
        self.log("\n" + "="*70, force=True)
        self.log("✅ 작업 완료", force=True)
        self.log("="*70, force=True)
        
        self.log(f"\n📊 통계:", force=True)
        self.log(f"   전체: {len(results)}개", force=True)
        self.log(f"   {'미리보기' if self.dry_run else '수정'}: {success_count}개", force=True)
        self.log(f"   실패: {failed_count}개", force=True)
        
        self.log(f"\n📋 수정 내역:", force=True)
        self.log(f"   필드: {fix_data['field_name']}", force=True)
        self.log(f"   대상 값: {', '.join(fix_data['target_values'])}", force=True)
        self.log(f"   변경 값: {fix_data['new_value']}", force=True)


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="JSON 필드 값 수정 도구",
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
        help='수정할 특정 폴더명 (생략 시 전체)'
    )
    parser.add_argument(
        '--field',
        required=True,
        help='수정할 필드명'
    )
    parser.add_argument(
        '--find',
        nargs='+',
        required=True,
        help='찾을 값들 (여러 개 가능)'
    )
    parser.add_argument(
        '--replace',
        required=True,
        help='변경할 값'
    )
    parser.add_argument(
        '--output-dir',
        default='fix_results',
        help='결과 저장 디렉토리 (기본: fix_results)'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='하위 폴더까지 재귀 탐색'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 수정 없이 미리보기만'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='백업 파일 생성 안함'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='최소한의 출력만 표시'
    )
    
    args = parser.parse_args()
    
    try:
        # 수정기 생성
        fixer = JSONFieldFixer(
            base_path=args.path,
            output_dir=args.output_dir,
            backup=not args.no_backup,
            dry_run=args.dry_run,
            quiet=args.quiet
        )
        
        # 수정 실행
        fix_data = fixer.fix_folders(
            folder_names=args.folders,
            field_name=args.field,
            target_values=args.find,
            new_value=args.replace,
            recursive=args.recursive
        )
        
        if fix_data and fix_data['results']:
            # 결과 저장
            fixer.save_results(fix_data)
            
            # 요약 출력
            fixer.print_summary(fix_data)
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
