FROM node:11

WORKDIR /app/
COPY package.json /app/

RUN npm install -g parcel-bundler
RUN npm install

COPY .postcssrc index.html /app/
COPY ./src /app/src

CMD parcel build -d /app/dist --public-url './' index.html
