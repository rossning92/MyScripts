sudo apt-get update

sudo apt install build-essential python3 git cmake bison flex \
    libffi-dev libxml2-dev libgdk-pixbuf2.0-dev libcairo2-dev \
    libpango1.0-dev fonts-lyx ghostscript libreadline-dev -y
	
sudo apt install ruby ruby-dev -y

sudo gem install --no-rdoc --no-ri asciidoctor coderay json-schema asciidoctor-mathematical asciidoctor-diagram
sudo gem install --no-rdoc --no-ri --pre asciidoctor-pdf