import subprocess

def run_scripts():
    subprocess.run(['python', 'Pdf_handler/pdftojson.py'], check=True)
    subprocess.run(['python', 'Pdf_handler/filler/fill_one.py'], check=True)

if __name__ == "__main__":
    run_scripts()