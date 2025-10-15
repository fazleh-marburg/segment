# CLIP

Run from Pycharm
cd /home/melahi/code/marburg/
python3 -m clip.main
python3 -m clip.zero_shot
python3 -m clip.linear_probe


# build the docker
docker build -t clip-text-image-matcher .

# run docker file
docker run -v /path/to/your/data:/home/melahi/code/image/segment/documents clip-text-image-matcher


# segment
# segment
