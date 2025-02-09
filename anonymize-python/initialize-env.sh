python3 -m venv mon_env
source mon_env/bin/activate
pip install Flask python-dotenv PyMuPDF
# Si vous avez un GPU compatible avec CUDA, utilisez la ligne juste après
# pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu117

# Sinon utilisez celle-ci
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu