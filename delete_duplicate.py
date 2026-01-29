import os
import hashlib

def file_hash(filepath):
    """Return SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def delete_duplicate_txt_files():
    current_dir = os.getcwd()
    txt_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.txt')]
    
    seen_hashes = {}
    deleted_files = []

    for filename in txt_files:
        filepath = os.path.join(current_dir, filename)
        try:
            filehash = file_hash(filepath)
            if filehash in seen_hashes:
                os.remove(filepath)
                deleted_files.append(filename)
                print(f"🗑️ Deleted duplicate: {filename}")
            else:
                seen_hashes[filehash] = filename
        except Exception as e:
            print(f"⚠️ Error reading {filename}: {e}")

    if not deleted_files:
        print("✅ No duplicate .txt files found.")
    else:
        print(f"\nDeleted {len(deleted_files)} duplicate file(s).")

if __name__ == "__main__":
    delete_duplicate_txt_files()
