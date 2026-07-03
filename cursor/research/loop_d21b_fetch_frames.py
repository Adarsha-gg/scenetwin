"""D21b — download the 60 external clips and extract frames for the visual-proxy fight at n=60.

Parses yt_id + start/end from each external clip id (e.g. 3ufJNSez5Is_000008_000018),
downloads just that segment at low res, extracts ~8 evenly spaced frames as JPGs.
Idempotent: skips clips already fetched. Prints a per-clip OK/FAIL log.
"""
import csv, os, sys, subprocess, glob
import imageio_ffmpeg

ROOT = r"C:\Users\adars\Coding\scenetwin"
OUT = os.path.join(ROOT, "cursor", "research", "output", "ext60_frames")
os.makedirs(OUT, exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
YTDLP = os.path.join(ROOT, ".venv_np", "Scripts", "yt-dlp.exe")
N_FRAMES = 8

def parse_id(vid):
    # <ytid>_<start6>_<end6>  ; ytid may contain underscores, times are last two 6-digit fields
    parts = vid.rsplit("_", 2)
    ytid, s, e = parts[0], int(parts[1]), int(parts[2])
    return ytid, s, e

def fetch(vid):
    ytid, s, e = parse_id(vid)
    cdir = os.path.join(OUT, vid)
    if len(glob.glob(os.path.join(cdir, "*.jpg"))) >= N_FRAMES:
        return "SKIP", vid
    os.makedirs(cdir, exist_ok=True)
    seg = os.path.join(cdir, "seg.mp4")
    if not os.path.exists(seg):
        cmd = [YTDLP, "-q", "--no-warnings", "-f", "worst[ext=mp4]/worst",
               "--download-sections", f"*{s}-{e}", "--force-keyframes-at-cuts",
               "--ffmpeg-location", FFMPEG, "-o", seg,
               f"https://www.youtube.com/watch?v={ytid}"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode != 0 or not os.path.exists(seg):
            return "DLFAIL", vid
    dur = max(1, e - s)
    fps_expr = f"fps={N_FRAMES}/{dur}"
    cmd2 = [FFMPEG, "-y", "-loglevel", "error", "-i", seg, "-vf", fps_expr,
            "-frames:v", str(N_FRAMES), os.path.join(cdir, "frame_%02d.jpg")]
    r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
    got = len(glob.glob(os.path.join(cdir, "*.jpg")))
    if got == 0:
        return "EXFAIL", vid
    try: os.remove(seg)
    except OSError: pass
    return f"OK({got})", vid

if __name__ == "__main__":
    ids = [r["video_id"] for r in csv.DictReader(
        open(os.path.join(ROOT, "cursor/output/halluc_gate/halluc_gate.csv")))]
    only = sys.argv[1:] if len(sys.argv) > 1 else ids
    ok = 0
    for i, vid in enumerate(only):
        try:
            status, _ = fetch(vid)
        except Exception as ex:
            status = f"ERR:{type(ex).__name__}"
        if status.startswith(("OK", "SKIP")): ok += 1
        print(f"[{i+1}/{len(only)}] {status:10s} {vid}", flush=True)
    print(f"\nDONE: {ok}/{len(only)} clips have >={N_FRAMES} frames in {OUT}")
