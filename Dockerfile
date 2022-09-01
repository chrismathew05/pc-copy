FROM public.ecr.aws/lambda/python@sha256:2342562ecf32e72dfad88f8267ad39d78f1d397415d47a4a208ac243f067dd67 as build

# install chrome and chromedriver to /opt/ directory
RUN yum install -y unzip && \
    curl -Lo "/tmp/chromedriver.zip" "https://chromedriver.storage.googleapis.com/101.0.4951.15/chromedriver_linux64.zip" && \
    curl -Lo "/tmp/chrome-linux.zip" "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F982481%2Fchrome-linux.zip?alt=media" && \
    unzip /tmp/chromedriver.zip -d /opt/ && \
    unzip /tmp/chrome-linux.zip -d /opt/

FROM public.ecr.aws/lambda/python@sha256:2342562ecf32e72dfad88f8267ad39d78f1d397415d47a4a208ac243f067dd67

# install required packages for lambda and chromedriver
RUN yum install atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel -y

# move chrome to final folders
COPY --from=build /opt/chrome-linux /opt/chrome
COPY --from=build /opt/chromedriver /opt/

# move and install program requirements
COPY src/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY src/ .

CMD [ "app/app.lambda_handler" ]