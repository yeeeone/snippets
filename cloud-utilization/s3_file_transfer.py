"""
S3 File Transfer Utility
=========================

S3 호환 스토리지와 로컬 파일 시스템 간 파일 업로드/다운로드를 수행하는 도구입니다.
(AWS S3, Naver Cloud Platform, MinIO 등 S3 호환 스토리지 지원)

사용법 (Usage)
-------------

1. 업로드 (Upload)
   
   # 전체 폴더 업로드
   $ python s3_file_transfer.py upload --local-path ./my_folder --s3-path my-project/data
   
   # 특정 폴더들만 선택 업로드
   $ python s3_file_transfer.py upload --local-path ./workers \
       --s3-path project/output \
       --folders folder1 folder2 folder3

2. 다운로드 (Download)
   
   # S3 폴더 전체 다운로드
   $ python s3_file_transfer.py download --s3-path my-project/data --local-path ./downloads
   
   # 특정 파일만 다운로드
   $ python s3_file_transfer.py download --s3-path my-project/data/file.txt --local-path ./downloads

3. 목록 조회 (List)
   
   # S3 경로의 파일/폴더 목록 출력
   $ python s3_file_transfer.py list --s3-path my-project/data
   
   # 재귀적으로 모든 파일 출력
   $ python s3_file_transfer.py list --s3-path my-project/data --recursive

설정 (Configuration)
--------------------

환경변수 또는 .env 파일에 다음 설정을 추가하세요:

S3_ENDPOINT_URL=https://s3.amazonaws.com  (AWS S3는 생략 가능)
S3_REGION=us-east-1
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET_NAME=your-bucket-name

AWS S3 사용 시:
  - S3_ENDPOINT_URL은 생략 (또는 비워두기)
  
Naver Cloud Platform 사용 시:
  - S3_ENDPOINT_URL=https://kr.object.ncloudstorage.com
  - S3_REGION=kr-standard

옵션 (Options)
--------------
  --endpoint-url URL    S3 엔드포인트 (환경변수로 설정 권장)
  --region REGION       리전 이름 (기본값: us-east-1)
  --bucket BUCKET       버킷 이름 (환경변수로 설정 권장)
  --local-path PATH     로컬 파일/폴더 경로
  --s3-path PATH        S3 경로 (버킷 내 경로)
  --folders NAMES       선택적 업로드할 폴더명 (공백으로 구분)
  --recursive           재귀적으로 모든 파일 처리
  --dry-run             실제 전송 없이 미리보기만 수행
  -h, --help            도움말 출력

예제 (Examples)
---------------

# 1. AWS S3에 폴더 업로드
$ export S3_BUCKET_NAME=my-bucket
$ export S3_ACCESS_KEY=AKIAXXXXXXXX
$ export S3_SECRET_KEY=xxxxxx
$ python s3_file_transfer.py upload --local-path ./data --s3-path project/data

# 2. NCP Object Storage에서 다운로드
$ export S3_ENDPOINT_URL=https://kr.object.ncloudstorage.com
$ export S3_REGION=kr-standard
$ export S3_BUCKET_NAME=my-bucket
$ python s3_file_transfer.py download --s3-path project/data --local-path ./downloads

# 3. 선택적 폴더 업로드
$ python s3_file_transfer.py upload \
    --local-path ./workers \
    --s3-path output/20250101 \
    --folders worker1 worker2 worker3

# 4. S3 목록 조회
$ python s3_file_transfer.py list --s3-path project/data --recursive

Author: [Your Name]
License: MIT
"""

import os
import sys
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import argparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env 파일이 없어도 환경변수로 설정 가능


class S3FileTransfer:
    """S3 호환 스토리지와 로컬 파일 시스템 간 파일 전송"""
    
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None
    ):
        """
        Args:
            endpoint_url: S3 엔드포인트 URL (AWS S3는 None)
            region: 리전 이름
            access_key: Access Key
            secret_key: Secret Key
            bucket_name: 버킷 이름
        """
        self.endpoint_url = endpoint_url or os.getenv("S3_ENDPOINT_URL")
        self.region = region or os.getenv("S3_REGION", "us-east-1")
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")
        
        access_key = access_key or os.getenv("S3_ACCESS_KEY")
        secret_key = secret_key or os.getenv("S3_SECRET_KEY")
        
        if not all([access_key, secret_key, self.bucket_name]):
            raise ValueError(
                "S3 설정이 필요합니다. 환경변수 또는 .env 파일에 "
                "S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME을 설정하세요."
            )
        
        # S3 클라이언트 생성
        client_config = {
            "service_name": "s3",
            "region_name": self.region,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "config": Config(s3={"addressing_style": "path"})
        }
        
        if self.endpoint_url:
            client_config["endpoint_url"] = self.endpoint_url
        
        self.s3 = boto3.client(**client_config)
        
        print(f"🔗 S3 연결:")
        if self.endpoint_url:
            print(f"   Endpoint: {self.endpoint_url}")
        print(f"   Region: {self.region}")
        print(f"   Bucket: {self.bucket_name}\n")
    
    def upload_file(self, local_path: str, s3_key: str, dry_run: bool = False) -> bool:
        """
        단일 파일을 S3에 업로드
        
        Args:
            local_path: 로컬 파일 경로
            s3_key: S3 키 (버킷 내 경로)
            dry_run: True면 실제 업로드 없이 미리보기만
            
        Returns:
            성공 여부
        """
        try:
            file_size = os.path.getsize(local_path)
            
            if dry_run:
                print(f"   [DRY-RUN] {local_path} -> s3://{self.bucket_name}/{s3_key}")
                return True
            
            self.s3.upload_file(local_path, self.bucket_name, s3_key)
            print(f"   ✓ {os.path.basename(local_path)} ({file_size / (1024*1024):.2f} MB)")
            return True
            
        except Exception as e:
            print(f"   ❌ {os.path.basename(local_path)}: {e}")
            return False
    
    def upload_folder(
        self,
        local_root: str,
        s3_base_path: str,
        dry_run: bool = False
    ) -> dict:
        """
        폴더 전체를 S3에 업로드
        
        Args:
            local_root: 로컬 폴더 경로
            s3_base_path: S3 기본 경로
            dry_run: True면 실제 업로드 없이 미리보기만
            
        Returns:
            업로드 통계 (uploaded_count, total_size, elapsed_time)
        """
        if not os.path.exists(local_root):
            print(f"❌ 경로가 존재하지 않습니다: {local_root}")
            return {"uploaded_count": 0, "total_size": 0}
        
        upload_start_time = datetime.now()
        uploaded_count = 0
        total_size = 0
        
        print(f"\n{'='*70}")
        print(f"📁 {'[DRY-RUN] ' if dry_run else ''}폴더 업로드")
        print(f"{'='*70}")
        print(f"📂 로컬: {local_root}")
        print(f"☁️  S3:   s3://{self.bucket_name}/{s3_base_path}/\n")
        
        for root, dirs, files in os.walk(local_root):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, local_root)
                s3_key = f"{s3_base_path}/{relative_path}".replace(os.sep, "/")
                
                file_size = os.path.getsize(local_path)
                total_size += file_size
                
                if self.upload_file(local_path, s3_key, dry_run):
                    uploaded_count += 1
        
        elapsed = datetime.now() - upload_start_time
        
        print(f"\n{'='*70}")
        print(f"✅ 업로드 완료!")
        print(f"{'='*70}")
        print(f"📊 파일 개수: {uploaded_count}개")
        print(f"📦 총 크기: {total_size / (1024*1024*1024):.2f} GB")
        print(f"⏱️  소요시간: {elapsed}\n")
        
        return {
            "uploaded_count": uploaded_count,
            "total_size": total_size,
            "elapsed_time": elapsed
        }
    
    def upload_specific_folders(
        self,
        base_dir: str,
        folder_names: List[str],
        s3_base_path: str,
        dry_run: bool = False
    ) -> dict:
        """
        특정 폴더들만 선택적으로 업로드
        
        Args:
            base_dir: 기본 디렉토리 경로
            folder_names: 업로드할 폴더명 리스트
            s3_base_path: S3 기본 경로
            dry_run: True면 실제 업로드 없이 미리보기만
            
        Returns:
            업로드 통계
        """
        print(f"\n{'='*70}")
        print(f"🎯 {'[DRY-RUN] ' if dry_run else ''}선택적 폴더 업로드")
        print(f"{'='*70}")
        print(f"📂 기본 경로: {base_dir}")
        print(f"📋 대상 폴더: {', '.join(folder_names)}\n")
        
        total_uploaded = 0
        total_size = 0
        upload_start_time = datetime.now()
        
        for folder_name in folder_names:
            folder_path = os.path.join(base_dir, folder_name)
            
            if not os.path.exists(folder_path):
                print(f"❗ 폴더를 찾을 수 없음: {folder_name}")
                continue
            
            if not os.path.isdir(folder_path):
                print(f"❗ 디렉토리가 아님: {folder_name}")
                continue
            
            print(f"\n📁 [{folder_name}] 업로드 중...")
            
            folder_uploaded = 0
            folder_size = 0
            
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, folder_path)
                    s3_key = f"{s3_base_path}/{folder_name}/{relative_path}".replace(os.sep, "/")
                    
                    file_size = os.path.getsize(local_path)
                    folder_size += file_size
                    
                    if self.upload_file(local_path, s3_key, dry_run):
                        folder_uploaded += 1
                        total_uploaded += 1
                        total_size += file_size
            
            print(f"   ✅ {folder_name}: {folder_uploaded}개 파일 ({folder_size / (1024*1024):.2f} MB)")
        
        elapsed = datetime.now() - upload_start_time
        
        print(f"\n{'='*70}")
        print(f"✅ 모든 업로드 완료!")
        print(f"{'='*70}")
        print(f"📊 총 파일: {total_uploaded}개")
        print(f"📦 총 크기: {total_size / (1024*1024*1024):.2f} GB")
        print(f"⏱️  소요시간: {elapsed}\n")
        
        return {
            "uploaded_count": total_uploaded,
            "total_size": total_size,
            "elapsed_time": elapsed
        }
    
    def download_file(self, s3_key: str, local_path: str, dry_run: bool = False) -> bool:
        """
        S3에서 단일 파일 다운로드
        
        Args:
            s3_key: S3 키
            local_path: 로컬 저장 경로
            dry_run: True면 실제 다운로드 없이 미리보기만
            
        Returns:
            성공 여부
        """
        try:
            if dry_run:
                print(f"   [DRY-RUN] s3://{self.bucket_name}/{s3_key} -> {local_path}")
                return True
            
            # 디렉토리 생성
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.s3.download_file(self.bucket_name, s3_key, local_path)
            file_size = os.path.getsize(local_path)
            print(f"   ✓ {os.path.basename(local_path)} ({file_size / (1024*1024):.2f} MB)")
            return True
            
        except Exception as e:
            print(f"   ❌ {os.path.basename(local_path)}: {e}")
            return False
    
    def download_folder(
        self,
        s3_prefix: str,
        local_root: str,
        dry_run: bool = False
    ) -> dict:
        """
        S3 폴더 전체를 로컬로 다운로드
        
        Args:
            s3_prefix: S3 경로 프리픽스
            local_root: 로컬 저장 경로
            dry_run: True면 실제 다운로드 없이 미리보기만
            
        Returns:
            다운로드 통계
        """
        download_start_time = datetime.now()
        downloaded_count = 0
        total_size = 0
        
        print(f"\n{'='*70}")
        print(f"📥 {'[DRY-RUN] ' if dry_run else ''}폴더 다운로드")
        print(f"{'='*70}")
        print(f"☁️  S3:   s3://{self.bucket_name}/{s3_prefix}/")
        print(f"📂 로컬: {local_root}\n")
        
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=s3_prefix)
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    s3_key = obj['Key']
                    relative_path = os.path.relpath(s3_key, s3_prefix)
                    local_path = os.path.join(local_root, relative_path)
                    
                    if self.download_file(s3_key, local_path, dry_run):
                        downloaded_count += 1
                        if not dry_run:
                            total_size += os.path.getsize(local_path)
            
            elapsed = datetime.now() - download_start_time
            
            print(f"\n{'='*70}")
            print(f"✅ 다운로드 완료!")
            print(f"{'='*70}")
            print(f"📊 파일 개수: {downloaded_count}개")
            print(f"📦 총 크기: {total_size / (1024*1024*1024):.2f} GB")
            print(f"⏱️  소요시간: {elapsed}\n")
            
            return {
                "downloaded_count": downloaded_count,
                "total_size": total_size,
                "elapsed_time": elapsed
            }
            
        except Exception as e:
            print(f"❌ 다운로드 중 오류: {e}")
            return {"downloaded_count": 0, "total_size": 0}
    
    def list_objects(self, s3_prefix: str = "", recursive: bool = False):
        """
        S3 경로의 객체 목록 출력
        
        Args:
            s3_prefix: S3 경로 프리픽스
            recursive: True면 재귀적으로 모든 파일 출력
        """
        print(f"\n{'='*70}")
        print(f"📋 S3 객체 목록")
        print(f"{'='*70}")
        print(f"☁️  경로: s3://{self.bucket_name}/{s3_prefix or '(root)'}\n")
        
        try:
            if recursive:
                # 모든 파일 나열
                paginator = self.s3.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=self.bucket_name, Prefix=s3_prefix)
                
                total_count = 0
                total_size = 0
                
                for page in pages:
                    if 'Contents' not in page:
                        continue
                    
                    for obj in page['Contents']:
                        size_mb = obj['Size'] / (1024*1024)
                        modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                        print(f"  📄 {obj['Key']}")
                        print(f"      크기: {size_mb:.2f} MB | 수정일: {modified}")
                        total_count += 1
                        total_size += obj['Size']
                
                print(f"\n{'='*70}")
                print(f"📊 총 파일: {total_count}개")
                print(f"📦 총 크기: {total_size / (1024*1024*1024):.2f} GB\n")
                
            else:
                # 디렉토리 구조만 나열
                response = self.s3.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=s3_prefix,
                    Delimiter='/'
                )
                
                # 폴더 출력
                if 'CommonPrefixes' in response:
                    print("📁 폴더:")
                    for prefix in response['CommonPrefixes']:
                        folder_name = prefix['Prefix'].rstrip('/').split('/')[-1]
                        print(f"  📁 {folder_name}/")
                
                # 파일 출력
                if 'Contents' in response:
                    print("\n📄 파일:")
                    for obj in response['Contents']:
                        if obj['Key'] == s3_prefix:  # 프리픽스 자체는 제외
                            continue
                        file_name = obj['Key'].split('/')[-1]
                        size_mb = obj['Size'] / (1024*1024)
                        print(f"  📄 {file_name} ({size_mb:.2f} MB)")
                
                print()
                
        except Exception as e:
            print(f"❌ 목록 조회 중 오류: {e}")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="S3 파일 전송 유틸리티 - 업로드/다운로드/목록조회",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='명령어')
    
    # 공통 인자
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--endpoint-url', help='S3 엔드포인트 URL')
    common.add_argument('--region', default='us-east-1', help='리전 (기본값: us-east-1)')
    common.add_argument('--bucket', help='버킷 이름')
    common.add_argument('--dry-run', action='store_true', help='실제 전송 없이 미리보기만')
    
    # upload 명령어
    upload_parser = subparsers.add_parser('upload', parents=[common], help='파일/폴더 업로드')
    upload_parser.add_argument('--local-path', required=True, help='로컬 경로')
    upload_parser.add_argument('--s3-path', required=True, help='S3 경로')
    upload_parser.add_argument('--folders', nargs='+', help='선택적 업로드할 폴더명')
    
    # download 명령어
    download_parser = subparsers.add_parser('download', parents=[common], help='파일/폴더 다운로드')
    download_parser.add_argument('--s3-path', required=True, help='S3 경로')
    download_parser.add_argument('--local-path', required=True, help='로컬 저장 경로')
    
    # list 명령어
    list_parser = subparsers.add_parser('list', parents=[common], help='S3 객체 목록')
    list_parser.add_argument('--s3-path', default='', help='S3 경로')
    list_parser.add_argument('--recursive', action='store_true', help='재귀적으로 모든 파일 출력')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # S3 클라이언트 생성
        transfer = S3FileTransfer(
            endpoint_url=args.endpoint_url,
            region=args.region,
            bucket_name=args.bucket
        )
        
        # 명령어 실행
        if args.command == 'upload':
            if args.folders:
                # 선택적 폴더 업로드
                transfer.upload_specific_folders(
                    args.local_path,
                    args.folders,
                    args.s3_path,
                    args.dry_run
                )
            else:
                # 전체 폴더 업로드
                transfer.upload_folder(
                    args.local_path,
                    args.s3_path,
                    args.dry_run
                )
        
        elif args.command == 'download':
            transfer.download_folder(
                args.s3_path,
                args.local_path,
                args.dry_run
            )
        
        elif args.command == 'list':
            transfer.list_objects(args.s3_path, args.recursive)
    
    except ValueError as e:
        print(f"❌ 설정 오류: {e}")
        print("\n환경변수를 설정하거나 .env 파일을 생성하세요:")
        print("  S3_ACCESS_KEY=your-access-key")
        print("  S3_SECRET_KEY=your-secret-key")
        print("  S3_BUCKET_NAME=your-bucket-name")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
