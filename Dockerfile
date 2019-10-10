FROM archlinux/base@sha256:9a482a9509a3eeb0571c0ccddccdc981cebe46e38861426f33a851dc504f7c4d
RUN pacman --noconfirm -Syyu git
#    && cd /tmp \
#    && git clone https://aur.archlinux.org/yay.git \
#    && cd yay \
#    && makepkg -si \
#    && useradd -m yay \
#    && rm -rf /tmp/yay


#RUN curl https://github.com/eomahony/Numberjack/archive/v1.2.0.tar.gz -L | tar -xz -C /build/ \
#    && ls -la /build/Numberjack-1.2.0 \
#    && cd /build/Numberjack-1.2.0 \
#    && pip install -e . -v

