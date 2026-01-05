#!/usr/bin/env python3
"""
서로 다른 두 개의 확장자 파일 개수 및 짝 확인 스크립트 

=== 사용법 ===

1. 기본 사용:
   python file_pair_checker.py

2. 설정 변경:
   main() 함수 내부의 변수를 수정하세요:
   
   target_directory = "/your/directory/path"  # 확인할 디렉토리 경로
   extension1 = "jpg"   # 첫 번째 확장자 (점 있어도/없어도 됨)
   extension2 = "json"  # 두 번째 확장자

3. 실행 결과:
   - 콘솔에 통계 정보 출력
   - file_pair_report_YYYYMMDD_HHMMSS.json 파일 생성
   
4. 출력 정보:
   - 완벽한 짝: 두 확장자가 모두 존재하는 파일 개수
   - 확장자1만 있음: 확장자1 파일만 있고 짝이 없는 개수
   - 확장자2만 있음: 확장자2 파일만 있고 짝이 없는 개수
   - 일치율: (완벽한 짝 / 전체 고유 파일명) × 100

=== 예시 ===

디렉토리 구조:
  photo_001.jpg
  photo_001.json  ✅ 짝 맞음
  photo_002.jpg   ❌ json 없음
  photo_003.json  ❌ jpg 없음

결과:
  완벽한 짝: 1개 (photo_001)
  JPG만 있음: 1개 (photo_002)
  JSON만 있음: 1개 (photo_003)
  일치율: 33.33% (1/3)
  
"""

import os
from pathlib import Path
import json
from datetime import datetime


def get_files_by_extension(directory, extension):
    """특정 확장자의 파일들을 수집"""
    # 확장자 정규화 (점 제거 및 소문자 변환)
    ext = extension.lower().lstrip('.')
    
    files = []
    for file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, file)):
            file_ext = os.path.splitext(file)[1].lower().lstrip('.')
            if file_ext == ext:
                files.append(file)
    return sorted(files)


def get_basename_without_ext(filename):
    """확장자를 제외한 파일명 반환"""
    return os.path.splitext(filename)[0]


def format_size(size_bytes):
    """파일 크기를 읽기 좋은 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def check_file_pairs(directory, ext1, ext2):
    """두 확장자 파일의 짝 확인"""
    
    # 확장자 정규화
    ext1_clean = ext1.lower().lstrip('.')
    ext2_clean = ext2.lower().lstrip('.')
    ext1_display = ext1_clean.upper()
    ext2_display = ext2_clean.upper()
    
    print("=" * 80)
    print("파일 짝 확인")
    print("=" * 80)
    print(f"\n대상 디렉토리: {directory}")
    print(f"확장자 1: .{ext1_clean}")
    print(f"확장자 2: .{ext2_clean}\n")
    
    if not os.path.exists(directory):
        print(f"❌ 디렉토리가 존재하지 않습니다: {directory}")
        return None
    
    # 파일 수집
    print("📂 파일 수집 중...")
    files_ext1 = get_files_by_extension(directory, ext1)
    files_ext2 = get_files_by_extension(directory, ext2)
    
    print(f"  .{ext1_clean} 파일: {len(files_ext1):,}개")
    print(f"  .{ext2_clean} 파일: {len(files_ext2):,}개")
    
    # 파일명(확장자 제외) 집합 생성
    basenames_ext1 = set(get_basename_without_ext(f) for f in files_ext1)
    basenames_ext2 = set(get_basename_without_ext(f) for f in files_ext2)
    
    # 짝 분석
    print(f"\n🔍 파일 짝 분석 중...")
    
    # 완벽한 짝
    perfect_pairs = basenames_ext1 & basenames_ext2
    
    # 확장자1만 있는 파일
    ext1_only = basenames_ext1 - basenames_ext2
    
    # 확장자2만 있는 파일
    ext2_only = basenames_ext2 - basenames_ext1
    
    # 일치율 계산 (전체 고유 파일명 대비 짝이 맞는 비율)
    total_unique = len(basenames_ext1 | basenames_ext2)
    match_rate = (len(perfect_pairs) / total_unique * 100) if total_unique > 0 else 0
    
    # 결과 출력
    print("\n" + "=" * 80)
    print("분석 결과")
    print("=" * 80)
    
    print(f"\n📊 전체 통계:")
    print(f"  완벽한 짝: {len(perfect_pairs):,}개")
    print(f"  .{ext1_clean}만 있음: {len(ext1_only):,}개")
    print(f"  .{ext2_clean}만 있음: {len(ext2_only):,}개")
    print(f"  총 고유 파일명: {total_unique:,}개")
    
    if len(ext1_only) == 0 and len(ext2_only) == 0:
        print("\n✅ 모든 파일의 짝이 완벽하게 맞습니다!")
    else:
        print("\n⚠️  일부 파일의 짝이 맞지 않습니다.")
    
    print(f"\n일치율: {match_rate:.2f}%")
    
    # 상세 내역
    details = {
        'checked_at': datetime.now().isoformat(),
        'directory': directory,
        'extensions': {
            'ext1': f".{ext1_clean}",
            'ext2': f".{ext2_clean}"
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
        'ext2_only_files': sorted(list(ext2_only))
    }
    
    # 확장자1만 있는 파일 출력
    if ext1_only:
        print(f"\n📄 .{ext1_clean}만 있는 파일 ({len(ext1_only):,}개):")
        print("-" * 80)
        for i, basename in enumerate(sorted(ext1_only)[:20], 1):
            print(f"  {i:3d}. {basename}.{ext1_clean}")
        if len(ext1_only) > 20:
            print(f"  ... 외 {len(ext1_only) - 20:,}개")
    
    # 확장자2만 있는 파일 출력
    if ext2_only:
        print(f"\n📄 .{ext2_clean}만 있는 파일 ({len(ext2_only):,}개):")
        print("-" * 80)
        for i, basename in enumerate(sorted(ext2_only)[:20], 1):
            print(f"  {i:3d}. {basename}.{ext2_clean}")
        if len(ext2_only) > 20:
            print(f"  ... 외 {len(ext2_only) - 20:,}개")
    
    # JSON 리포트 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f"file_pair_report_{timestamp}.json"
    
    try:
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(details, f, ensure_ascii=False, indent=2)
        print(f"\n💾 상세 리포트가 저장되었습니다: {json_filename}")
    except Exception as e:
        print(f"\n❌ 리포트 저장 실패: {e}")
    
    # 샘플 파일 확인 (처음 5개)
    if perfect_pairs:
        print(f"\n✅ 짝이 맞는 파일 샘플 (처음 5개):")
        print("-" * 80)
        for i, basename in enumerate(sorted(perfect_pairs)[:5], 1):
            file1_path = os.path.join(directory, f"{basename}.{ext1_clean}")
            file2_path = os.path.join(directory, f"{basename}.{ext2_clean}")
            
            # 파일 크기 확인
            try:
                size1 = os.path.getsize(file1_path)
                size2 = os.path.getsize(file2_path)
                
                print(f"  {i}. {basename}")
                print(f"     .{ext1_clean}: {format_size(size1)} | .{ext2_clean}: {format_size(size2)}")
            except Exception as e:
                print(f"  {i}. {basename} - ⚠️ 파일 크기 확인 실패: {e}")
    
    return details


def main():
    print("=" * 80)
    print("파일 짝 확인 스크립트")
    print("=" * 80)
    print()
    
    # 경로 설정
    target_directory = "/your/directory/path"
    
    # 확장자 설정 (점 포함 여부 상관없음)
    extension1 = "jpg"  # 또는 ".jpg"
    extension2 = "json"  # 또는 ".json"
    
    # 디렉토리 존재 확인
    if not os.path.exists(target_directory):
        print(f"❌ 오류: 디렉토리가 존재하지 않습니다: {target_directory}")
        print("\n경로를 확인해주세요.")
        return
    
    # 파일 짝 확인
    result = check_file_pairs(target_directory, extension1, extension2)
    
    if result:
        print("\n" + "=" * 80)
        print("확인 완료!")
        print("=" * 80)
        
        # 간단한 요약
        summary = result['summary']
        if summary['ext1_only'] == 0 and summary['ext2_only'] == 0:
            print("\n🎉 완벽합니다! 모든 파일의 짝이 맞습니다.")
        else:
            print(f"\n⚠️  누락된 파일: {summary['ext1_only'] + summary['ext2_only']:,}개")
            print(f"   - .{extension1}만: {summary['ext1_only']:,}개")
            print(f"   - .{extension2}만: {summary['ext2_only']:,}개")


if __name__ == "__main__":
    main()