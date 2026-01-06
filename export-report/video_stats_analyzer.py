"""
Video Statistics Analyzer
==========================

JSON 매니페스트 파일에서 비디오 길이 통계를 분석하고 리포트를 생성하는 도구입니다.

사용법 (Usage)
-------------

1. 기본 사용 (모든 폴더 분석)
   $ python video_stats_analyzer.py

2. 날짜 범위로 분석
   $ python video_stats_analyzer.py --start-date 20250901 --end-date 20250930
   $ python video_stats_analyzer.py --start-date 20250901  # 시작일 이후 전부
   $ python video_stats_analyzer.py --end-date 20250930    # 종료일 이전 전부

3. 폴더 목록 확인 (분석 없이 목록만 출력)
   $ python video_stats_analyzer.py --list
   $ python video_stats_analyzer.py --list --start-date 20250901

4. 이미 처리된 폴더 재분석
   $ python video_stats_analyzer.py --reprocess
   $ python video_stats_analyzer.py --reprocess --start-date 20250901

5. 커스텀 경로 지정
   $ python video_stats_analyzer.py --base-path ./my_videos --output-dir ./my_stats

옵션 (Options)
--------------
  --base-path PATH      업로드 폴더가 있는 기본 경로 (기본값: data/uploads)
  --output-dir PATH     통계 결과를 저장할 디렉토리 (기본값: stats_output)
  --start-date DATE     시작 날짜 (YYYYMMDD 형식, 예: 20250901)
  --end-date DATE       종료 날짜 (YYYYMMDD 형식, 예: 20250930)
  --list                폴더 목록만 출력 (분석 안함)
  --reprocess           이미 처리된 폴더도 다시 처리
  -h, --help            도움말 출력

디렉토리 구조 (Directory Structure)
-----------------------------------
project/
├── data/
│   └── uploads/
│       ├── upload_20250829_001/
│       │   └── manifests/
│       │       ├── video1.json
│       │       └── video2.json
│       ├── upload_20250901_002/
│       └── upload_20250915_003/
├── stats_output/          # 자동 생성됨
│   ├── processed_folders.json
│   ├── video_stats_upload_20250829_001.csv
│   ├── video_durations_raw_upload_20250829_001.csv
│   └── invalid_files_upload_20250829_001.csv
└── video_stats_analyzer.py

JSON 형식 요구사항
------------------
매니페스트 JSON 파일은 다음 형식을 포함해야 합니다:
{
  "duration": "HH:MM:SS",
  ...
}

출력 파일 (Output Files)
------------------------
1. video_stats_*.csv           - 폴더별 통계 요약
2. video_durations_raw_*.csv   - 개별 비디오 길이 원본 데이터
3. invalid_files_*.csv         - 처리 실패한 파일 목록
4. processed_folders.json      - 처리 완료된 폴더 추적 로그

"""

import os
import json
import statistics
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import List, Optional, Tuple


class VideoStatsAnalyzer:
    """
    비디오 통계 분석기
    - 로컬 폴더에서 JSON 매니페스트 파일을 읽어 영상 길이 통계를 생성합니다
    - 날짜 범위를 지정하여 특정 기간의 데이터만 분석할 수 있습니다
    """
    
    def __init__(self, base_path: str = "data/uploads", output_dir: str = "stats_output"):
        """
        Args:
            base_path: 업로드 폴더들이 있는 기본 경로
            output_dir: 통계 결과를 저장할 디렉토리
        """
        self.base_path = Path(base_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.processed_log_file = self.output_dir / "processed_folders.json"
        self.processed_folders = self.load_processed_folders()
    
    def load_processed_folders(self) -> set:
        """처리된 폴더 목록을 로드"""
        if self.processed_log_file.exists():
            with open(self.processed_log_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()
    
    def save_processed_folders(self):
        """처리된 폴더 목록을 저장"""
        with open(self.processed_log_file, 'w', encoding='utf-8') as f:
            json.dump(sorted(list(self.processed_folders)), f, indent=2, ensure_ascii=False)
    
    def extract_date_from_folder(self, folder_name: str) -> Optional[str]:
        """
        폴더명에서 날짜를 추출
        예: 'upload_20250829_001' -> '20250829'
        
        Args:
            folder_name: 폴더명
            
        Returns:
            YYYYMMDD 형식의 날짜 문자열 또는 None
        """
        match = re.search(r'(\d{8})', folder_name)
        if match:
            return match.group(1)
        return None
    
    def is_folder_in_date_range(
        self, 
        folder_name: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> bool:
        """
        폴더가 지정된 날짜 범위 내에 있는지 확인
        
        Args:
            folder_name: 폴더명
            start_date: 시작 날짜 (YYYYMMDD 형식), None이면 제한 없음
            end_date: 종료 날짜 (YYYYMMDD 형식), None이면 제한 없음
            
        Returns:
            날짜 범위 내에 있으면 True
        """
        folder_date = self.extract_date_from_folder(folder_name)
        
        if folder_date is None:
            print(f"⚠️ 폴더명에서 날짜를 추출할 수 없음: {folder_name}")
            return False
        
        if start_date and folder_date < start_date:
            return False
        
        if end_date and folder_date > end_date:
            return False
        
        return True
    
    def get_upload_folders(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Path]:
        """
        업로드 폴더 목록을 가져오기
        
        Args:
            start_date: 시작 날짜 (YYYYMMDD)
            end_date: 종료 날짜 (YYYYMMDD)
            
        Returns:
            필터링된 폴더 경로 리스트
        """
        if not self.base_path.exists():
            print(f"❌ 기본 경로가 존재하지 않습니다: {self.base_path}")
            return []
        
        all_folders = [f for f in self.base_path.iterdir() if f.is_dir()]
        
        # 날짜 범위 필터링
        filtered_folders = [
            folder for folder in all_folders
            if self.is_folder_in_date_range(folder.name, start_date, end_date)
        ]
        
        if start_date or end_date:
            date_info = f"{start_date or '시작'} ~ {end_date or '종료'}"
            print(f"📅 전체 폴더: {len(all_folders)}개 → 필터링 후: {len(filtered_folders)}개 ({date_info})")
        else:
            print(f"📂 전체 폴더: {len(all_folders)}개")
        
        return sorted(filtered_folders)
    
    def parse_duration(self, duration_str: str) -> int:
        """
        duration 문자열을 초 단위로 변환
        
        Args:
            duration_str: "HH:MM:SS" 형식의 문자열
            
        Returns:
            초 단위 시간
        """
        try:
            t = datetime.strptime(duration_str, "%H:%M:%S")
            delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
            return int(delta.total_seconds())
        except Exception as e:
            print(f"⚠️ 잘못된 duration 형식: {duration_str} - {e}")
            return 0
    
    def seconds_to_hms(self, seconds: int) -> str:
        """
        초를 시:분:초 형태로 변환
        
        Args:
            seconds: 초 단위 시간
            
        Returns:
            "H:MM:SS" 형식의 문자열
        """
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours}:{minutes:02d}:{secs:02d}"
    
    def get_json_files_from_folder(self, folder_path: Path) -> List[Path]:
        """
        특정 폴더의 manifests 디렉토리에서 모든 JSON 파일 목록을 가져오기
        
        Args:
            folder_path: 폴더 경로
            
        Returns:
            JSON 파일 경로 리스트
        """
        manifests_dir = folder_path / "manifests"
        
        if not manifests_dir.exists():
            return []
        
        return list(manifests_dir.glob("*.json"))
    
    def process_folder(self, folder_path: Path) -> bool:
        """
        특정 폴더의 영상 길이 통계를 처리
        
        Args:
            folder_path: 처리할 폴더 경로
            
        Returns:
            처리 성공 여부
        """
        folder_name = folder_path.name
        folder_date = self.extract_date_from_folder(folder_name)
        
        print(f"\n{'='*60}")
        print(f"폴더 처리 시작: {folder_name} ({folder_date})")
        print(f"{'='*60}")
        
        # JSON 파일 목록 가져오기
        json_files = self.get_json_files_from_folder(folder_path)
        print(f"JSON 파일 발견: {len(json_files)}개")
        
        if not json_files:
            print(f"⚠️ 폴더 {folder_name}에서 JSON 파일을 찾을 수 없습니다.")
            return False
        
        # 영상 길이 및 유효하지 않은 파일 추적
        durations_seconds = []
        invalid_files = []
        
        print(f"JSON 파일 읽는 중... (총 {len(json_files)}개 파일)")
        
        for i, json_file in enumerate(json_files, 1):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                duration_str = data.get('duration', None)
                if duration_str:
                    duration_seconds = self.parse_duration(duration_str)
                    if duration_seconds > 0:
                        durations_seconds.append(duration_seconds)
                    else:
                        invalid_files.append({
                            'file': json_file.name,
                            'reason': 'parse_duration returned 0',
                            'duration_str': duration_str
                        })
                else:
                    invalid_files.append({
                        'file': json_file.name,
                        'reason': 'no duration field',
                        'data_keys': ', '.join(data.keys())
                    })
                
                # 진행상황 표시
                if i % 100 == 0 or i == len(json_files):
                    print(f"진행중... {i}/{len(json_files)} 파일 처리 완료")
                    
            except Exception as e:
                print(f"⚠️ 파일 처리 중 오류 발생 ({json_file.name}): {e}")
                invalid_files.append({
                    'file': json_file.name,
                    'reason': f'Exception: {str(e)}'
                })
        
        # 유효하지 않은 파일 로그
        if invalid_files:
            print(f"\n⚠️ 유효하지 않은 파일: {len(invalid_files)}개")
            for invalid in invalid_files[:10]:
                print(f"  - {invalid['file']}: {invalid['reason']}")
            if len(invalid_files) > 10:
                print(f"  ... 외 {len(invalid_files) - 10}개")
            
            # 유효하지 않은 파일 목록 저장
            invalid_csv_path = self.output_dir / f"invalid_files_{folder_name}.csv"
            invalid_df = pd.DataFrame(invalid_files)
            invalid_df.to_csv(invalid_csv_path, index=False, encoding='utf-8-sig')
            print(f"  → 상세 정보 저장: {invalid_csv_path}")
        
        if not durations_seconds:
            print(f"⚠️ 폴더 {folder_name}에서 유효한 영상 길이 데이터를 찾을 수 없습니다.")
            return False
        
        # 통계 계산
        total_videos = len(durations_seconds)
        total_duration_seconds = sum(durations_seconds)
        average_duration_seconds = total_duration_seconds / total_videos
        min_duration_seconds = min(durations_seconds)
        max_duration_seconds = max(durations_seconds)
        median_duration_seconds = statistics.median(durations_seconds)
        
        # 길이별 분포 계산
        ranges = [
            (0, 60), (60, 300), (300, 600), (600, 1800),
            (1800, 2400), (2400, 3000), (3000, 3600), (3600, float('inf'))
        ]
        range_labels = [
            "1분 미만", "5분 미만", "10분 미만", "30분 미만",
            "40분 미만", "50분 미만", "60분 미만", "1시간 이상"
        ]
        
        distribution = {}
        for (min_sec, max_sec), label in zip(ranges, range_labels):
            count = len([d for d in durations_seconds if min_sec <= d < max_sec])
            percentage = (count / total_videos) * 100
            distribution[f"{label}_개수"] = count
            distribution[f"{label}_비율"] = round(percentage, 1)
        
        # 통계 데이터를 CSV로 저장
        stats_data = {
            "폴더명": [folder_name],
            "폴더날짜": [folder_date],
            "처리시간": [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            "발견된_JSON_파일": [len(json_files)],
            "유효한_파일": [total_videos],
            "무효한_파일": [len(invalid_files)],
            "총_영상_개수": [total_videos],
            "총_영상_시간_초": [total_duration_seconds],
            "총_영상_시간_HMS": [self.seconds_to_hms(total_duration_seconds)],
            "평균_길이_초": [round(average_duration_seconds, 2)],
            "평균_길이_HMS": [self.seconds_to_hms(average_duration_seconds)],
            "최소_길이_초": [min_duration_seconds],
            "최소_길이_HMS": [self.seconds_to_hms(min_duration_seconds)],
            "최대_길이_초": [max_duration_seconds],
            "최대_길이_HMS": [self.seconds_to_hms(max_duration_seconds)],
            "중간값_초": [median_duration_seconds],
            "중간값_HMS": [self.seconds_to_hms(median_duration_seconds)]
        }
        
        # 분포 데이터 추가
        stats_data.update({key: [value] for key, value in distribution.items()})
        
        # DataFrame 생성 및 CSV 저장
        stats_df = pd.DataFrame(stats_data)
        csv_path = self.output_dir / f"video_stats_{folder_name}.csv"
        stats_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # 개별 영상 길이 데이터도 저장
        durations_df = pd.DataFrame(durations_seconds, columns=["duration_sec"])
        durations_csv_path = self.output_dir / f"video_durations_raw_{folder_name}.csv"
        durations_df.to_csv(durations_csv_path, index=False)
        
        # 결과 출력
        print(f"\n✅ 영상 길이 통계 분석 결과 - {folder_name}")
        print("="*50)
        print(f"폴더 날짜: {folder_date}")
        print(f"발견된 JSON 파일: {len(json_files)}개")
        print(f"유효한 파일: {total_videos}개")
        print(f"무효한 파일: {len(invalid_files)}개")
        print(f"총 영상 개수: {total_videos}개")
        print(f"총 영상 시간: {self.seconds_to_hms(total_duration_seconds)}")
        print(f"평균 길이: {self.seconds_to_hms(average_duration_seconds)}")
        print(f"최소 길이: {self.seconds_to_hms(min_duration_seconds)}")
        print(f"최대 길이: {self.seconds_to_hms(max_duration_seconds)}")
        print(f"중간값: {self.seconds_to_hms(median_duration_seconds)}")
        print("="*50)
        
        # 길이별 분포 출력
        print(f"\n📊 길이 분포:")
        for (min_sec, max_sec), label in zip(ranges, range_labels):
            count = len([d for d in durations_seconds if min_sec <= d < max_sec])
            percentage = (count / total_videos) * 100
            print(f"  {label}: {count}개 ({percentage:.1f}%)")
        
        print(f"\n💾 결과 저장 완료:")
        print(f"  - 통계 CSV: {csv_path}")
        print(f"  - 원본 데이터 CSV: {durations_csv_path}")
        if invalid_files:
            print(f"  - 무효 파일 목록: {invalid_csv_path}")
        
        return True
    
    def analyze_folders(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        skip_processed: bool = True
    ):
        """
        폴더들을 분석하고 통계를 생성
        
        Args:
            start_date: 시작 날짜 (YYYYMMDD)
            end_date: 종료 날짜 (YYYYMMDD)
            skip_processed: 이미 처리된 폴더를 건너뛸지 여부
        """
        folders = self.get_upload_folders(start_date, end_date)
        
        if not folders:
            print("❌ 분석할 폴더가 없습니다.")
            return
        
        print(f"\n🚀 총 {len(folders)}개의 폴더 분석을 시작합니다...")
        
        success_count = 0
        skip_count = 0
        
        for i, folder in enumerate(folders, 1):
            folder_name = folder.name
            
            if skip_processed and folder_name in self.processed_folders:
                print(f"\n[{i}/{len(folders)}] ⏭️ 이미 처리된 폴더: {folder_name}")
                skip_count += 1
                continue
            
            print(f"\n[{i}/{len(folders)}] 처리 중: {folder_name}")
            
            if self.process_folder(folder):
                self.processed_folders.add(folder_name)
                success_count += 1
        
        self.save_processed_folders()
        
        print(f"\n{'='*60}")
        print(f"✅ 분석 완료!")
        print(f"  - 성공: {success_count}개")
        print(f"  - 건너뜀: {skip_count}개")
        print(f"  - 전체 처리된 폴더: {len(self.processed_folders)}개")
        print(f"{'='*60}")
    
    def list_folders(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ):
        """
        폴더 목록 출력
        
        Args:
            start_date: 시작 날짜 (YYYYMMDD)
            end_date: 종료 날짜 (YYYYMMDD)
        """
        folders = self.get_upload_folders(start_date, end_date)
        
        if not folders:
            print("❌ 폴더가 없습니다.")
            return
        
        print(f"\n📂 폴더 목록 ({len(folders)}개):")
        print("="*60)
        
        for i, folder in enumerate(folders, 1):
            folder_name = folder.name
            folder_date = self.extract_date_from_folder(folder_name)
            processed = "✓" if folder_name in self.processed_folders else " "
            print(f"[{processed}] {i}. {folder_name} ({folder_date})")
        
        print("="*60)
        print(f"✓ = 이미 처리된 폴더")


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="비디오 통계 분석기 - JSON 매니페스트에서 영상 길이 통계를 생성합니다."
    )
    parser.add_argument(
        '--base-path',
        default='data/uploads',
        help='업로드 폴더들이 있는 기본 경로 (기본값: data/uploads)'
    )
    parser.add_argument(
        '--output-dir',
        default='stats_output',
        help='통계 결과를 저장할 디렉토리 (기본값: stats_output)'
    )
    parser.add_argument(
        '--start-date',
        help='시작 날짜 (YYYYMMDD 형식, 예: 20250901)'
    )
    parser.add_argument(
        '--end-date',
        help='종료 날짜 (YYYYMMDD 형식, 예: 20250930)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='폴더 목록만 출력'
    )
    parser.add_argument(
        '--reprocess',
        action='store_true',
        help='이미 처리된 폴더도 다시 처리'
    )
    
    args = parser.parse_args()
    
    # 분석기 생성
    analyzer = VideoStatsAnalyzer(
        base_path=args.base_path,
        output_dir=args.output_dir
    )
    
    # 폴더 목록만 출력
    if args.list:
        analyzer.list_folders(
            start_date=args.start_date,
            end_date=args.end_date
        )
    # 분석 실행
    else:
        analyzer.analyze_folders(
            start_date=args.start_date,
            end_date=args.end_date,
            skip_processed=not args.reprocess
        )


if __name__ == "__main__":
    main()

