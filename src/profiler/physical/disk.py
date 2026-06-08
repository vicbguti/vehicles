import os
from glob import glob
from typing import Dict, Any, List

def profile_disk_files(pattern: str) -> Dict[str, Any]:
    """
    Scans files matching the glob pattern and profiles their physical size on disk.
    """
    files = glob(pattern)
    file_profiles: List[Dict[str, Any]] = []
    total_bytes = 0
    
    for file_path in sorted(files):
        if os.path.isfile(file_path):
            size_bytes = os.path.getsize(file_path)
            total_bytes += size_bytes
            file_profiles.append({
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2)
            })
            
    return {
        "total_files": len(file_profiles),
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "files": file_profiles
    }
