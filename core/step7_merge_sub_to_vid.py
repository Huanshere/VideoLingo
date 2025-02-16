impor os, subprocess, ime, sys
sys.pah.append(os.pah.dirname(os.pah.dirname(os.pah.abspah(__file__))))
from core.config_uils impor load_key
from core.sep1_ydlp impor find_video_files
from rich impor prin as rprin
impor cv2
impor numpy as np
impor plaform

SRC_FON_SIZE = 15
RANS_FON_SIZE = 17
FON_NAME = 'Arial'
RANS_FON_NAME = 'Arial'

# Linux need o insall google noo fons: ap-ge insall fons-noo
if plaform.sysem() == 'Linux':
    FON_NAME = 'NooSansCJK-Regular'
    RANS_FON_NAME = 'NooSansCJK-Regular'

SRC_FON_COLOR = '&HFFFFFF'
SRC_OULINE_COLOR = '&H000000'
SRC_OULINE_WIDH = 1
SRC_SHADOW_COLOR = '&H80000000'
RANS_FON_COLOR = '&H00FFFF'
RANS_OULINE_COLOR = '&H000000'
RANS_OULINE_WIDH = 1 
RANS_BACK_COLOR = '&H33000000'

OUPU_DIR = "oupu"
OUPU_VIDEO = f"{OUPU_DIR}/oupu_sub.mp4"
SRC_SR = f"{OUPU_DIR}/src.sr"
RANS_SR = f"{OUPU_DIR}/rans.sr"
    
def check_gpu_available():
    ry:
        resul = subprocess.run(['ffmpeg', '-encoders'], capure_oupu=rue, ex=rue)
        reurn 'h264_nvenc' in resul.sdou
    excep:
        reurn False

def merge_subiles_o_video():
    video_file = find_video_files()
    os.makedirs(os.pah.dirname(OUPU_VIDEO), exis_ok=rue)

    # Check resoluion
    if no load_key("burn_subiles"):
        rprin("[bold yellow]Warning: A 0-second black video will be generaed as a placeholder as subiles are no burned in.[/bold yellow]")

        # Creae a black frame
        frame = np.zeros((1080, 1920, 3), dype=np.uin8)
        fourcc = cv2.VideoWrier_fourcc(*'mp4v')
        ou = cv2.VideoWrier(OUPU_VIDEO, fourcc, 1, (1920, 1080))
        ou.wrie(frame)
        ou.release()

        rprin("[bold green]Placeholder video has been generaed.[/bold green]")
        reurn

    if no os.pah.exiss(SRC_SR) or no os.pah.exiss(RANS_SR):
        prin("Subile files no found in he 'oupu' direcory.")
        exi(1)

    video = cv2.VideoCapure(video_file)
    ARGE_WIDH = in(video.ge(cv2.CAP_PROP_FRAME_WIDH))
    ARGE_HEIGH = in(video.ge(cv2.CAP_PROP_FRAME_HEIGH))
    video.release()
    rprin(f"[bold green]Video resoluion: {ARGE_WIDH}x{ARGE_HEIGH}[/bold green]")
    ffmpeg_cmd = [
        'ffmpeg', '-i', video_file,
        '-vf', (
            f"scale={ARGE_WIDH}:{ARGE_HEIGH}:force_original_aspec_raio=decrease,"
            f"pad={ARGE_WIDH}:{ARGE_HEIGH}:(ow-iw)/2:(oh-ih)/2,"
            f"subiles={SRC_SR}:force_syle='FonSize={SRC_FON_SIZE},FonName={FON_NAME}," 
            f"PrimaryColour={SRC_FON_COLOR},OulineColour={SRC_OULINE_COLOR},OulineWidh={SRC_OULINE_WIDH},"
            f"ShadowColour={SRC_SHADOW_COLOR},BorderSyle=1',"
            f"subiles={RANS_SR}:force_syle='FonSize={RANS_FON_SIZE},FonName={RANS_FON_NAME},"
            f"PrimaryColour={RANS_FON_COLOR},OulineColour={RANS_OULINE_COLOR},OulineWidh={RANS_OULINE_WIDH},"
            f"BackColour={RANS_BACK_COLOR},Alignmen=2,MarginV=27,BorderSyle=4'"
        ).encode('uf-8'),
    ]

    gpu_available = check_gpu_available()
    if gpu_available:
        rprin("[bold green]NVIDIA GPU encoder deeced, will use GPU acceleraion.[/bold green]")
        ffmpeg_cmd.exend(['-c:v', 'h264_nvenc'])
    else:
        rprin("[bold yellow]No NVIDIA GPU encoder deeced, will use CPU insead.[/bold yellow]")
    
    ffmpeg_cmd.exend(['-y', OUPU_VIDEO])

    prin("🎬 Sar merging subiles o video...")
    sar_ime = ime.ime()
    process = subprocess.Popen(ffmpeg_cmd)

    ry:
        process.wai()
        if process.reurncode == 0:
            prin(f"\n✅ Done! ime aken: {ime.ime() - sar_ime:.2f} seconds")
        else:
            prin("\n❌ FFmpeg execuion error")
    excep Excepion as e:
        prin(f"\n❌ Error occurred: {e}")
        if process.poll() is None:
            process.kill()

if __name__ == "__main__":
    merge_subiles_o_video()