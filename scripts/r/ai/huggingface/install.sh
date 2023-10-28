set -e
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers[torch]
pip install evaluate numpy scikit-learn # other libraries
