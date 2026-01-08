#!/usr/bin/env python3
"""
File Pair Checker
=================

서로 다른 확장자 파일의 쌍을 검증하는 도구입니다.
단일 폴더 또는 서로 다른 두 폴더에서 파일 쌍을 확인할 수 있습니다.

사용법 (Usage)
-------------

1. 단일 폴더 모드 (같은 경로에 두 확장자 파일)
   $ python file_pair_checker.py --mode single \
       --path ./data/upload_001 \
       --ext1 mp4 --ext2 json

2. 이중 폴더 모드 (서로 다른 경로에 파일)
   $ python file_pair_checker.py --mode dual \
       --path1 ./videos \
       --path2 ./manifests \
       --ext1 mp4 --ext2 json

3. 출력 디렉토리 지정
   $ python file_pair_checker.py --mode single \
       --path ./data \
       --ext1 jpg --ext2 json \
       --output-dir ./check_results

기능 (Features)
---------------
✓ 단일 폴더에서 파일 쌍 검증
✓ 서로 다른 두 폴더 간 파일 쌍 검증
✓ 누락/매칭 파일 상세 리포트
✓ JSON/TXT 형식 결과 저장
✓ 파일 크기 정보 포함

출력 예시 (Output)
------------------
pair_check_results/
├── file_pair_report_20250106_143022.txt   # 텍스트 리포트
└── file_pair_report_20250106_143022.json  # JSON 리포트

디렉토리 구조 예시 (Directory Structure)
----------------------------------------

# 단일 폴더 모드
data/
├── video_001.mp4
├── video_001.json  ✅ 짝 맞음
├── video_002.mp4   ❌ json 없음
└── video_003.json  ❌ mp4 없음

# 이중 폴더 모드
videos/
├── video_001.mp4
├── video_002.mp4
└── video_003.mp4   ❌ manifest 없음

manifests/
├── video_001.json
├── video_002.json
└── video_004.json  ❌ video 없음

옵션 (Options)
--------------
  --mode MODE          검증 모드: single (단일 폴더) 또는 dual (이중 폴더)
  --path PATH          [single 모드] 검증할 폴더 경로
  --path1 PATH         [dual 모드] 첫 번째 폴더 경로
  --path2 PATH         [dual 모드] 두 번째 폴더 경로
  --ext1 EXT           첫 번째 확장자 (예: mp4, jpg)
  --ext2 EXT           두 번째 확장자 (예: json)
  --output-dir DIR     결과 저장 디렉토리 (기본: pair_check_results)
  -h, --help           도움말 출력

"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, List, Tuple


class FilePairChecker:
    """파일 쌍 검증 클래스"""
    
    def __init__(self, output_dir: str = "pair_check_results"):
        """
        Args:
            output_dir: 결과 저장 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
    
    @staticmethod
    def get_files_by_extension(directory: Path, extension: str) -> List[str]:
        """
        특정 확장자의 파일들을 수집
        
        Args:
            directory: 탐색할 디렉토리
            extension: 확장자 (점 있어도/없어도 됨)
            
        Returns:
            파일명 리스트
        """
        ext = extension.lower().lstrip('.')
        files = []
        
        if not directory.exists():
            return files
        
        for file in directory.iterdir():
            if file.is_file():
                file_ext = file.suffix.lower().lstrip('.')
                if file_ext == ext:
                    files.append(file.name)
        
        return sorted(files)
    
    @staticmethod
    def get_basename_without_ext(filename: str) -> str:
        """확장자를 제외한 파일명 반환"""
        return Path(filename).stem
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """파일 크기를 읽기 좋은 형식으로 변환"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def check_single_folder(
        self,
        directory: Path,
        ext1: str,
        ext2: str
    ) -> Dict:
        """
        단일 폴더에서 두 확장자 파일의 쌍 확인
        
        Args:
            directory: 검증할 디렉토리
            ext1: 첫 번째 확장자
            ext2: 두 번째 확장자
            
        Returns:
            검증 결과 딕셔너리
        """
        ext1_clean = ext1.lower().lstrip('.')
        ext2_clean = ext2.lower().lstrip('.')
        
        print("=" * 80)
        print("📋 단일 폴더 파일 쌍 검증")
        print("=" * 80)
        print(f"\n대상 디렉토리: {directory}")
        print(f"확장자 1: .{ext1_clean}")
        print(f"확장자 2: .{ext2_clean}\n")
        
        if not directory.exists():
            print(f"❌ 디렉토리가 존재하지 않습니다: {directory}")
            return None
        
        # 파일 수집
        print("📂 파일 수집 중...")
        files_ext1 = self.get_files_by_extension(directory, ext1)
        files_ext2 = self.get_files_by_extension(directory, ext2)
        
        print(f"  .{ext1_clean} 파일: {len(files_ext1):,}개")
        print(f"  .{ext2_clean} 파일: {len(files_ext2):,}개")
        
        # 파일명(확장자 제외) 집합 생성
        basenames_ext1 = set(self.get_basename_without_ext(f) for f in files_ext1)
        basenames_ext2 = set(self.get_basename_without_ext(f) for f in files_ext2)
        
        # 짝 분석
        print(f"\n🔍 파일 짝 분석 중...")
        
        perfect_pairs = basenames_ext1 & basenames_ext2
        ext1_only = basenames_ext1 - basenames_ext2
        ext2_only = basenames_ext2 - basenames_ext1
        
        # 일치율 계산
        total_unique = len(basenames_ext1 | basenames_ext2)
        match_rate = (len(perfect_pairs) / total_unique * 100) if total_unique > 0 else 0
        
        # 결과 반환
        return self._format_result(
            directory, None, ext1_clean, ext2_clean,
            files_ext1, files_ext2, perfect_pairs, ext1_only, ext2_only,
            total_unique, match_rate, "single"
        )
    
    def check_dual_folders(
        self,
        directory1: Path,
        directory2: Path,
        ext1: str,
        ext2: str
    ) -> Dict:
        """
        서로 다른 두 폴더에서 파일 쌍 확인
        
        Args:
            directory1: 첫 번째 디렉토리 (ext1 파일 위치)
            directory2: 두 번째 디렉토리 (ext2 파일 위치)
            ext1: 첫 번째 확장자
            ext2: 두 번째 확장자
            
        Returns:
            검증 결과 딕셔너리
        """
        ext1_clean = ext1.lower().lstrip('.')
        ext2_clean = ext2.lower().lstrip('.')
        
        print("=" * 80)
        print("📋 이중 폴더 파일 쌍 검증")
        print("=" * 80)
        print(f"\n폴더 1 (.{ext1_clean}): {directory1}")
        print(f"폴더 2 (.{ext2_clean}): {directory2}\n")
        
        if not directory1.exists():
            print(f"❌ 디렉토리가 존재하지 않습니다: {directory1}")
            return None
        
        if not directory2.exists():
            print(f"❌ 디렉토리가 존재하지 않습니다: {directory2}")
            return None
        
        # 파일 수집
        print("📂 파일 수집 중...")
        files_ext1 = self.get_files_by_extension(directory1, ext1)
        files_ext2 = self.get_files_by_extension(directory2, ext2)
        
        print(f"  폴더 1의 .{ext1_clean} 파일: {len(files_ext1):,}개")
        print(f"  폴더 2의 .{ext2_clean} 파일: {len(files_ext2):,}개")
        
        # 파일명(확장자 제외) 집합 생성
        basenames_ext1 = set(self.get_basename_without_ext(f) for f in files_ext1)
        basenames_ext2 = set(self.get_basename_without_ext(f) for f in files_ext2)
        
        # 짝 분석
        print(f"\n🔍 파일 짝 분석 중...")
        
        perfect_pairs = basenames_ext1 & basenames_ext2
        ext1_only = basenames_ext1 - basenames_ext2
        ext2_only = basenames_ext2 - basenames_ext1
        
        # 일치율 계산
        total_unique = len(basenames_ext1 | basenames_ext2)
        match_rate = (len(perfect_pairs) / total_unique * 100) if total_unique > 0 else 0
        
        # 결과 반환
        return self._format_result(
            directory1, directory2, ext1_clean, ext2_clean,
            files_ext1, files_ext2, perfect_pairs, ext1_only, ext2_only,
            total_unique, match_rate, "dual"
        )
    
    def _format_result(
        self,
        dir1: Path,
        dir2: Path,
        ext1: str,
        ext2: str,
        files_ext1: List[str],
        files_ext2: List[str],
        perfect_pairs: Set[str],
        ext1_only: Set[str],
        ext2_only: Set[str],
        total_unique: int,
        match_rate: float,
        mode: str
    ) -> Dict:
        """결과 포맷팅 및 출력"""
        
        # 콘솔 출력
        print("\n" + "=" * 80)
        print("분석 결과")
        print("=" * 80)
        
        print(f"\n📊 전체 통계:")
        print(f"  완벽한 짝: {len(perfect_pairs):,}개")
        print(f"  .{ext1}만 있음: {len(ext1_only):,}개")
        print(f"  .{ext2}만 있음: {len(ext2_only):,}개")
        print(f"  총 고유 파일명: {total_unique:,}개")
        
        if len(ext1_only) == 0 and len(ext2_only) == 0:
            print("\n✅ 모든 파일의 짝이 완벽하게 맞습니다!")
        else:
            print("\n⚠️  일부 파일의 짝이 맞지 않습니다.")
        
        print(f"\n📈 일치율: {match_rate:.2f}%")
        
        # 상세 내역
        details = {
            'checked_at': datetime.now().isoformat(),
            'mode': mode,
            'directories': {
                'dir1': str(dir1),
                'dir2': str(dir2) if dir2 else None
            },
            'extensions': {
                'ext1': f".{ext1}",
                'ext2': f".{ext2}"
            },
            'summary': {
                'ext1_count': len(files_ext1),
                'ext2_count': len(files_ext2),
                'perfect_pairs': len(perfect_pairs),
                'ext1_only': len(ext1_only),
                'ext2_only': len(ext2_only),
                'total_unique': total_unique,
                'match_rate_percent': round(match_rate, 2)
            },
            'ext1_only_files': sorted(list(ext1_only)),
            'ext2_only_files': sorted(list(ext2_only)),
            'perfect_pairs_sample': sorted(list(perfect_pairs))[:100]  # 처음 100개만
        }
        
        # ext1만 있는 파일 출력
        if ext1_only:
            print(f"\n📄 .{ext1}만 있는 파일 ({len(ext1_only):,}개):")
            print("-" * 80)
            for i, basename in enumerate(sorted(ext1_only)[:20], 1):
                print(f"  {i:3d}. {basename}.{ext1}")
            if len(ext1_only) > 20:
                print(f"  ... 외 {len(ext1_only) - 20:,}개")
        
        # ext2만 있는 파일 출력
        if ext2_only:
            print(f"\n📄 .{ext2}만 있는 파일 ({len(ext2_only):,}개):")
            print("-" * 80)
            for i, basename in enumerate(sorted(ext2_only)[:20], 1):
                print(f"  {i:3d}. {basename}.{ext2}")
            if len(ext2_only) > 20:
                print(f"  ... 외 {len(ext2_only) - 20:,}개")
        
        # 짝이 맞는 파일 샘플
        if perfect_pairs:
            print(f"\n✅ 짝이 맞는 파일 샘플 (처음 5개):")
            print("-" * 80)
            for i, basename in enumerate(sorted(perfect_pairs)[:5], 1):
                if mode == "single":
                    file1_path = dir1 / f"{basename}.{ext1}"
                    file2_path = dir1 / f"{basename}.{ext2}"
                else:
                    file1_path = dir1 / f"{basename}.{ext1}"
                    file2_path = dir2 / f"{basename}.{ext2}"
                
                try:
                    size1 = file1_path.stat().st_size
                    size2 = file2_path.stat().st_size
                    
                    print(f"  {i}. {basename}")
                    print(f"     .{ext1}: {self.format_size(size1)} | .{ext2}: {self.format_size(size2)}")
                except Exception as e:
                    print(f"  {i}. {basename} - ⚠️ 파일 크기 확인 실패")
        
        return details
    
    def save_results(self, details: Dict):
        """
        결과를 파일로 저장
        
        Args:
            details: 검증 결과 딕셔너리
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON 리포트
        json_file = self.output_dir / f"file_pair_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(details, f, ensure_ascii=False, indent=2)
        
        # 텍스트 리포트
        txt_file = self.output_dir / f"file_pair_report_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("파일 쌍 검증 리포트\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"검증 시간: {details['checked_at']}\n")
            f.write(f"검증 모드: {details['mode']}\n")
            f.write(f"폴더 1: {details['directories']['dir1']}\n")
            if details['directories']['dir2']:
                f.write(f"폴더 2: {details['directories']['dir2']}\n")
            f.write(f"확장자 1: {details['extensions']['ext1']}\n")
            f.write(f"확장자 2: {details['extensions']['ext2']}\n\n")
            
            summary = details['summary']
            f.write("=" * 80 + "\n")
            f.write("통계\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"완벽한 짝: {summary['perfect_pairs']:,}개\n")
            f.write(f"{details['extensions']['ext1']}만 있음: {summary['ext1_only']:,}개\n")
            f.write(f"{details['extensions']['ext2']}만 있음: {summary['ext2_only']:,}개\n")
            f.write(f"총 고유 파일명: {summary['total_unique']:,}개\n")
            f.write(f"일치율: {summary['match_rate_percent']:.2f}%\n\n")
            
            # 누락 파일 목록
            if details['ext1_only_files']:
                f.write("=" * 80 + "\n")
                f.write(f"{details['extensions']['ext1']}만 있는 파일 목록\n")
                f.write("=" * 80 + "\n\n")
                for basename in details['ext1_only_files']:
                    f.write(f"{basename}{details['extensions']['ext1']}\n")
                f.write("\n")
            
            if details['ext2_only_files']:
                f.write("=" * 80 + "\n")
                f.write(f"{details['extensions']['ext2']}만 있는 파일 목록\n")
                f.write("=" * 80 + "\n\n")
                for basename in details['ext2_only_files']:
                    f.write(f"{basename}{details['extensions']['ext2']}\n")
        
        print(f"\n💾 결과 저장:")
        print(f"   JSON: {json_file}")
        print(f"   Text: {txt_file}")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="파일 쌍 검증 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--mode',
        required=True,
        choices=['single', 'dual'],
        help='검증 모드: single (단일 폴더) 또는 dual (이중 폴더)'
    )
    parser.add_argument(
        '--path',
        help='[single 모드] 검증할 폴더 경로'
    )
    parser.add_argument(
        '--path1',
        help='[dual 모드] 첫 번째 폴더 경로'
    )
    parser.add_argument(
        '--path2',
        help='[dual 모드] 두 번째 폴더 경로'
    )
    parser.add_argument(
        '--ext1',
        required=True,
        help='첫 번째 확장자 (예: mp4, jpg)'
    )
    parser.add_argument(
        '--ext2',
        required=True,
        help='두 번째 확장자 (예: json)'
    )
    parser.add_argument(
        '--output-dir',
        default='pair_check_results',
        help='결과 저장 디렉토리 (기본: pair_check_results)'
    )
    
    args = parser.parse_args()
    
    # 입력 검증
    if args.mode == 'single' and not args.path:
        parser.error("--mode single 사용 시 --path가 필요합니다")
    
    if args.mode == 'dual' and (not args.path1 or not args.path2):
        parser.error("--mode dual 사용 시 --path1과 --path2가 모두 필요합니다")
    
    try:
        # 검증기 생성
        checker = FilePairChecker(output_dir=args.output_dir)
        
        # 검증 실행
        if args.mode == 'single':
            result = checker.check_single_folder(
                Path(args.path),
                args.ext1,
                args.ext2
            )
        else:  # dual
            result = checker.check_dual_folders(
                Path(args.path1),
                Path(args.path2),
                args.ext1,
                args.ext2
            )
        
        if result:
            # 결과 저장
            checker.save_results(result)
            
            # 최종 요약
            print("\n" + "=" * 80)
            print("✅ 검증 완료!")
            print("=" * 80)
            
            summary = result['summary']
            if summary['ext1_only'] == 0 and summary['ext2_only'] == 0:
                print("\n🎉 완벽합니다! 모든 파일의 짝이 맞습니다.")
            else:
                print(f"\n⚠️  누락된 파일: {summary['ext1_only'] + summary['ext2_only']:,}개")
                print(f"   - {result['extensions']['ext1']}만: {summary['ext1_only']:,}개")
                print(f"   - {result['extensions']['ext2']}만: {summary['ext2_only']:,}개")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
